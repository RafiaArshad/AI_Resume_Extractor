# # app/services/extractor.py
# """
# Main resume parsing pipeline.

# Priority:
#   1. Regex / rule-based extraction for reliable fields
#      (contact info, skills vocabulary, domain)
#   2. LLM (Ollama) for summary, experience, education, projects
#      when available and returning valid JSON
#   3. Structured regex fallback for every field when LLM is offline

# Return schema (all keys always present):
#   basic_info     : {name, emails, phones, location, links}
#   summary        : str
#   education      : [{institution, degree, field, duration,
#                      start_year, end_year, gpa, coursework}]
#   experience     : [{role, company, duration, start_year, end_year,
#                      is_current, responsibilities}]
#   projects       : [{name, description, tech_stack, links}]
#   skills         : {technical, languages, frameworks, tools}
#                      — each item: {name, confidence}
#                      — "other" category suppressed
#   soft_skills    : [str]   — no scores, plain names only
#   domain         : {name, confidence, breakdown}
#   certifications : [{name, issuer, date, credential_id, url}]
#   awards         : [str]
#   spoken_languages: [str]
#   extraction_method: str
# """

# import logging
# import os
# import re
# from typing import Any, Dict, List, Optional

# import fitz           # PyMuPDF
# import docx
# from fastapi import HTTPException

# from app.services.utils import (
#     clean_text,
#     SECTION_HEADERS,
#     is_heading,
#     extract_emails,
#     extract_phones,
#     extract_links,
#     extract_location,
#     extract_name_fallback,
#     parse_experience_section,
#     parse_education_section,
#     parse_certifications_section,
#     parse_projects_section,
#     extract_skills_rule_based,
#     clean_summary,
#     validate_llm_experience,
#     SKILL_VOCABULARY,
# )
# from app.services.skill_scoring import (
#     classify_domain,
#     score_skills,
#     extract_soft_skills,
# )
# from app.services.ollama_extractor import extract_with_ollama

# logger = logging.getLogger(__name__)


# # ============================================================
# # TEXT EXTRACTION
# # ============================================================

# def extract_text_from_pdf(file_path: str) -> str:
#     parts: List[str] = []
#     try:
#         with fitz.open(file_path) as doc:
#             for page in doc:
#                 t = page.get_text("text")
#                 if t.strip():
#                     parts.append(t)
#     except Exception as e:
#         logger.error("PDF extraction error: %s", e)
#         raise HTTPException(500, f"Failed to read PDF: {e}")
#     return "\n".join(parts)


# def extract_text_from_docx(file_path: str) -> str:
#     try:
#         doc = docx.Document(file_path)
#         return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
#     except Exception as e:
#         logger.error("DOCX extraction error: %s", e)
#         raise HTTPException(500, f"Failed to read DOCX: {e}")


# def extract_text(file_path: str) -> str:
#     ext = os.path.splitext(file_path)[1].lower()
#     if ext == ".pdf":
#         raw = extract_text_from_pdf(file_path)
#     elif ext == ".docx":
#         raw = extract_text_from_docx(file_path)
#     else:
#         raise HTTPException(400, f"Unsupported file type: {ext}. Allowed: pdf, docx")
#     return clean_text(raw)


# # ============================================================
# # SECTION SPLITTING
# # ============================================================

# def split_sections(text: str) -> Dict[str, List[str]]:
#     """Split text into named sections; lines before first heading → summary."""
#     sections: Dict[str, List[str]] = {k: [] for k in SECTION_HEADERS}
#     sections["other"] = []
#     current = "summary"
#     for raw in text.split("\n"):
#         line = raw.strip()
#         if not line:
#             continue
#         h = is_heading(line)
#         if h:
#             current = h
#             continue
#         sections[current].append(line)
#     return sections


# # ============================================================
# # MERGE HELPERS
# # ============================================================

# def _merge_unique(a: List[str], b: List[str]) -> List[str]:
#     seen: set = set()
#     result: List[str] = []
#     for item in a + b:
#         key = item.strip().lower()
#         if key and key not in seen:
#             seen.add(key)
#             result.append(item.strip())
#     return result


# def _best_str(llm_val: Any, fallback: str) -> str:
#     if isinstance(llm_val, str) and llm_val.strip():
#         return llm_val.strip()
#     return fallback


# def _safe_list(val: Any) -> List:
#     return val if isinstance(val, list) and val else []


# # ============================================================
# # SKILLS  — merge regex vocabulary with LLM discoveries, then score
# # ============================================================

# def _merge_and_score_skills(
#     regex_skills: Dict[str, List[str]],
#     llm_skills: Any,
#     full_text: str,
# ) -> Dict:
#     """
#     1. Start with regex-detected skills (guaranteed to be in vocabulary).
#     2. Add any NEW skills the LLM found that aren't already in the bucket.
#     3. Score everything with score_skills (which drops the "other" category).
#     """
#     merged: Dict[str, List[str]] = {cat: list(items) for cat, items in regex_skills.items()}

#     if isinstance(llm_skills, dict):
#         for cat in ("technical", "languages", "frameworks", "tools"):
#             llm_items = _safe_list(llm_skills.get(cat, []))
#             existing_lower = {s.lower() for s in merged.get(cat, [])}
#             for item in llm_items:
#                 if isinstance(item, str) and item.strip():
#                     if item.strip().lower() not in existing_lower:
#                         merged.setdefault(cat, []).append(item.strip())
#                         existing_lower.add(item.strip().lower())

#     return score_skills(merged, full_text)


# # ============================================================
# # EXPERIENCE
# # ============================================================

# def _get_experience(llm: Dict, fallback_lines: List[str]) -> List[Dict]:
#     llm_exp = llm.get("experience")
#     if isinstance(llm_exp, list) and llm_exp:
#         validated = validate_llm_experience(llm_exp)
#         if validated:
#             return validated
#     return parse_experience_section(fallback_lines)


# # ============================================================
# # EDUCATION
# # ============================================================

# def _get_education(llm: Dict, fallback_lines: List[str]) -> List[Dict]:
#     llm_edu = llm.get("education")
#     if isinstance(llm_edu, list) and llm_edu:
#         if all(isinstance(e, dict) and e.get("institution") for e in llm_edu):
#             return [
#                 {
#                     "institution": e.get("institution", ""),
#                     "degree":      e.get("degree", ""),
#                     "field":       e.get("field", ""),
#                     "duration":    e.get("duration", ""),
#                     "start_year":  e.get("start_year"),
#                     "end_year":    e.get("end_year"),
#                     "gpa":         e.get("gpa"),
#                     "coursework":  e.get("coursework", []),
#                 }
#                 for e in llm_edu
#             ]
#         if all(isinstance(e, str) for e in llm_edu):
#             return parse_education_section(llm_edu)
#     return parse_education_section(fallback_lines)


# # ============================================================
# # CERTIFICATIONS  (structured, LLM-augmented)
# # ============================================================

# def _get_certifications(llm: Dict, section_lines: List[str]) -> List[Dict]:
#     parsed = parse_certifications_section(section_lines)

#     llm_certs = _safe_list(llm.get("certifications", []))
#     existing  = {c["name"].lower() for c in parsed if c.get("name")}
#     extras: List[Dict] = []

#     for item in llm_certs:
#         if isinstance(item, str) and item.strip():
#             if item.strip().lower() not in existing:
#                 extras.append({
#                     "name": item.strip(), "issuer": None,
#                     "date": None, "credential_id": None, "url": None,
#                 })
#                 existing.add(item.strip().lower())
#         elif isinstance(item, dict) and item.get("name"):
#             nm = item["name"].strip()
#             if nm.lower() not in existing:
#                 extras.append({
#                     "name":          nm,
#                     "issuer":        item.get("issuer"),
#                     "date":          item.get("date"),
#                     "credential_id": item.get("credential_id"),
#                     "url":           item.get("url"),
#                 })
#                 existing.add(nm.lower())

#     return parsed + extras


# # ============================================================
# # PROJECTS  (structured, LLM preferred)
# # ============================================================

# def _get_projects(llm: Dict, section_lines: List[str], skill_vocab: Optional[Dict] = None) -> List[Dict]:
#     llm_proj = _safe_list(llm.get("projects", []))

#     if llm_proj:
#         if all(isinstance(p, dict) for p in llm_proj):
#             structured = []
#             for p in llm_proj:
#                 name = str(p.get("name", "") or "").strip()
#                 desc = p.get("description", "")
#                 if isinstance(desc, str):
#                     desc = [desc] if desc.strip() else []
#                 elif isinstance(desc, list):
#                     desc = [str(d) for d in desc if str(d).strip()]
#                 tech  = _safe_list(p.get("tech_stack") or p.get("technologies") or [])
#                 links = _safe_list(p.get("links") or [])
#                 if name or desc:
#                     structured.append({
#                         "name":        name,
#                         "description": desc,
#                         "tech_stack":  [str(t) for t in tech  if t],
#                         "links":       [str(lk) for lk in links if lk],
#                     })
#             if structured:
#                 return structured
#         if all(isinstance(p, str) for p in llm_proj):
#             return parse_projects_section(llm_proj, skill_vocab)

#     return parse_projects_section(section_lines, skill_vocab)


# # ============================================================
# # SUMMARY
# # ============================================================

# def _get_summary(llm: Dict, section_lines: List[str]) -> str:
#     llm_sum = llm.get("summary", "")
#     if isinstance(llm_sum, str) and len(llm_sum.strip()) > 40:
#         return clean_summary(llm_sum)
#     return clean_summary(" ".join(section_lines))


# # ============================================================
# # AWARDS
# # ============================================================

# def _get_awards(llm: Dict, section_lines: List[str]) -> List[str]:
#     regex_awards = [l.strip() for l in section_lines if l.strip()]
#     llm_awards   = [str(a) for a in _safe_list(llm.get("awards")) if isinstance(a, str)]
#     merged = _merge_unique(regex_awards, llm_awards)
#     return [re.sub(r"^[•\-\*◦▪●]\s*", "", a).strip() for a in merged if a.strip()]


# # ============================================================
# # MAIN PIPELINE
# # ============================================================

# def parse_resume(file_path: str) -> Dict:
#     """
#     Full pipeline. Returns structured dict ready for storage + frontend.
#     """
#     # ── Step 1: Raw text ──────────────────────────────────────────────────────
#     text = extract_text(file_path)
#     if not text or len(text.strip()) < 50:
#         raise HTTPException(400, "Could not extract readable text from the document")
#     logger.info("Extracted %d chars from %s", len(text), os.path.basename(file_path))

#     # ── Step 2: Section splitting ─────────────────────────────────────────────
#     sections = split_sections(text)

#     # ── Step 3: Reliable regex extraction ────────────────────────────────────
#     regex_name = extract_name_fallback(text) or ""
#     emails     = extract_emails(text)
#     phones     = extract_phones(text)
#     links      = extract_links(text)
#     location   = extract_location(text)
#     raw_skills = extract_skills_rule_based(text)
#     soft_skills = extract_soft_skills(text)
#     domain      = classify_domain(sections, text)

#     # ── Step 4: LLM extraction (optional, non-blocking) ───────────────────────
#     llm: Dict = {}
#     try:
#         llm = extract_with_ollama(text) or {}
#     except Exception:
#         logger.warning("Ollama extraction raised unexpectedly — continuing without LLM")
#         llm = {}

#     llm_ok    = bool(llm and isinstance(llm, dict) and llm.get("basic_info"))
#     llm_basic = llm.get("basic_info", {}) if llm_ok else {}
#     active    = llm if llm_ok else {}

#     # ── Step 5: Contact info (regex authoritative for emails/phones) ──────────
#     name = _best_str(llm_basic.get("name"), regex_name)

#     # Filter LLM emails: must contain '@'
#     llm_emails = [
#         e for e in _safe_list(llm_basic.get("emails"))
#         if isinstance(e, str) and "@" in e
#     ]
#     merged_emails = _merge_unique(emails, llm_emails)
#     merged_phones = _merge_unique(phones, _safe_list(llm_basic.get("phones")))
#     merged_links  = _merge_unique(links,  _safe_list(llm_basic.get("links")))

#     # Location: prefer LLM if it found one, else regex
#     llm_location = llm_basic.get("location") if llm_ok else None
#     final_location = (
#         (llm_location if isinstance(llm_location, str) and llm_location.strip() else None)
#         or location
#     )

#     basic_info = {
#         "name":     name,
#         "emails":   merged_emails,
#         "phones":   merged_phones,
#         "location": final_location,
#         "links":    merged_links,
#     }

#     # ── Step 6: Summary ───────────────────────────────────────────────────────
#     summary = _get_summary(active, sections.get("summary", []))

#     # ── Step 7: Experience ────────────────────────────────────────────────────
#     experience = _get_experience(active, sections.get("experience", []))

#     # ── Step 8: Education ─────────────────────────────────────────────────────
#     education = _get_education(active, sections.get("education", []))

#     # ── Step 9: Projects ──────────────────────────────────────────────────────
#     projects = _get_projects(active, sections.get("projects", []), SKILL_VOCABULARY)

#     # ── Step 10: Skills (merge regex + LLM, then score; "other" suppressed) ───
#     llm_skills = llm.get("skills") if llm_ok else None
#     skills = _merge_and_score_skills(raw_skills, llm_skills, text)

#     # ── Step 11: Certifications ───────────────────────────────────────────────
#     certifications = _get_certifications(active, sections.get("certifications", []))

#     # ── Step 12: Awards ───────────────────────────────────────────────────────
#     awards = _get_awards(active, sections.get("awards", []))

#     # ── Step 13: Human languages ──────────────────────────────────────────────
#     spoken_languages = [
#         line.strip()
#         for line in sections.get("languages", [])
#         if line.strip()
#     ]

#     return {
#         "basic_info":        basic_info,
#         "summary":           summary,
#         "education":         education,
#         "experience":        experience,
#         "projects":          projects,
#         "skills":            skills,
#         "soft_skills":       soft_skills,
#         "domain":            domain,
#         "certifications":    certifications,
#         "awards":            awards,
#         "spoken_languages":  spoken_languages,
#         "extraction_method": "hybrid_llm_rule" if llm_ok else "regex_rule",
#     }













# # app/services/extractor.py
# """
# Production Resume Parsing Pipeline (Crash‑Proof)

# Key guarantees:
# • Regex-first extraction for reliability
# • LLM enrichment is optional & safe
# • Unified skills block (no duplication)
# • Languages split into high_level / low_level
# • Soft skills unscored
# • Projects NEVER crash parser
# """

# import logging
# import os
# import re
# from typing import Dict, List, Any

# import fitz
# import docx
# from fastapi import HTTPException

# from app.services.utils import (
#     clean_text,
#     SECTION_HEADERS,
#     is_heading,
#     extract_emails,
#     extract_phones,
#     extract_links,
#     extract_location,
#     extract_name_fallback,
#     parse_experience_section,
#     parse_education_section,
#     parse_projects_section,
#     parse_certifications_section,
#     extract_skills_rule_based,
#     clean_summary,
#     validate_llm_experience,
#     SKILL_VOCABULARY,
# )

# from app.services.skill_scoring import (
#     classify_domain,
#     score_skills,
#     extract_soft_skills,
# )

# from app.services.ollama_extractor import extract_with_ollama

# logger = logging.getLogger(__name__)

# # ============================================================
# # Language classification
# # ============================================================

# HIGH_LEVEL_LANGUAGES = {
#     # General-purpose
#     "python", "java", "javascript", "typescript", "c#", "f#", "vb.net",
#     "php", "ruby", "go", "kotlin", "swift", "dart", "julia", "scala",
#     "groovy", "objective-c",

#     # Scientific / data
#     "r", "matlab", "sas", "stata",

#     # Functional
#     "haskell", "erlang", "elixir", "ocaml", "clojure", "lisp", "scheme",

#     # Scripting (treated as high-level)
#     "bash", "shell", "sh", "zsh", "ksh", "powershell", "perl", "awk", "tcl",

#     # Web / markup (commonly expected in resumes)
#     "html", "css", "sass", "scss",

#     # Query / database
#     "sql", "plsql", "tsql",

#     # Others
#     "fortran", "cobol", "ada", "crystal", "nim", "smalltalk"
# }


# LOW_LEVEL_LANGUAGES = {
#     # True low-level
#     "assembly", "asm", "machine code",

#     # Systems programming (close to hardware)
#     "c", "c++",

#     # Modern systems languages (low-level control)
#     "rust", "zig", "v"
# }

# # ============================================================
# # Text extraction
# # ============================================================

# def extract_text(file_path: str) -> str:
#     ext = os.path.splitext(file_path)[1].lower()

#     try:
#         if ext == ".pdf":
#             with fitz.open(file_path) as doc:
#                 text = "\n".join(
#                     page.get_text("text")
#                     for page in doc
#                     if page.get_text().strip()
#                 )
#         elif ext == ".docx":
#             doc = docx.Document(file_path)
#             text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
#         else:
#             raise HTTPException(400, "Unsupported file type")
#     except Exception as e:
#         raise HTTPException(500, f"Failed to extract text: {e}")

#     text = clean_text(text)
#     if len(text) < 50:
#         raise HTTPException(400, "Unreadable resume content")

#     return text

# # ============================================================
# # Section splitting
# # ============================================================

# def split_sections(text: str) -> Dict[str, List[str]]:
#     sections = {k: [] for k in SECTION_HEADERS}
#     sections["summary"] = []

#     current = "summary"

#     for raw in text.splitlines():
#         line = raw.strip()
#         if not line:
#             continue

#         header = is_heading(line)
#         if header:
#             current = header
#             continue

#         sections.setdefault(current, []).append(line)

#     return sections

# # ============================================================
# # Skills (unified + scored)
# # ============================================================

# def split_language_levels(scored_langs: List[Dict]) -> Dict[str, List[Dict]]:
#     high, low = [], []

#     for lang in scored_langs:
#         name = lang.get("name", "").lower()
#         if name in LOW_LEVEL_LANGUAGES:
#             low.append(lang)
#         else:
#             high.append(lang)

#     return {"high_level": high, "low_level": low}


# def build_unified_skills(
#     regex_skills: Dict[str, List[str]],
#     llm_skills: Any,
#     full_text: str,
#     soft_skills: List[str],
# ) -> Dict:

#     merged = {k: list(v) for k, v in regex_skills.items()}

#     if isinstance(llm_skills, dict):
#         for cat in ("technical", "languages", "frameworks", "tools"):
#             existing = {s.lower() for s in merged.get(cat, [])}
#             for item in llm_skills.get(cat, []):
#                 name = item if isinstance(item, str) else item.get("name", "")
#                 if name and name.lower() not in existing:
#                     merged.setdefault(cat, []).append(name)
#                     existing.add(name.lower())

#     scored = score_skills(merged, full_text)

#     return {
#         "technical": scored.get("technical", []),
#         "languages": split_language_levels(scored.get("languages", [])),
#         "frameworks": scored.get("frameworks", []),
#         "tools": scored.get("tools", []),
#         "soft_skills": sorted(set(soft_skills)),
#     }

# # ============================================================
# # Main pipeline
# # ============================================================

# def parse_resume(file_path: str) -> Dict:
#     text = extract_text(file_path)
#     sections = split_sections(text)

#     # ── Regex extraction ───────────────────────────────────
#     name = extract_name_fallback(text) or ""
#     emails = extract_emails(text)
#     phones = extract_phones(text)
#     links = extract_links(text)
#     location = extract_location(text)

#     regex_skills = extract_skills_rule_based(text)
#     soft_skills = extract_soft_skills(text)
#     domain = classify_domain(sections, text)

#     # ── LLM extraction (safe) ─────────────────────────────
#     try:
#         llm = extract_with_ollama(text) or {}
#     except Exception:
#         llm = {}

#     llm_basic = llm.get("basic_info", {}) if isinstance(llm, dict) else {}

#     # ── Contact info merge ────────────────────────────────
#     def merge_unique(a, b):
#         seen = set()
#         out = []
#         for x in a + b:
#             k = str(x).lower()
#             if k and k not in seen:
#                 seen.add(k)
#                 out.append(x)
#         return out

#     basic_info = {
#         "name": llm_basic.get("name") or name,
#         "emails": merge_unique(emails, llm_basic.get("emails", [])),
#         "phones": merge_unique(phones, llm_basic.get("phones", [])),
#         "links": merge_unique(links, llm_basic.get("links", [])),
#         "location": llm_basic.get("location") or location,
#     }

#     # ── Summary ───────────────────────────────────────────
#     summary = (
#         clean_summary(llm.get("summary"))
#         if isinstance(llm.get("summary"), str)
#         else clean_summary(" ".join(sections.get("summary", [])))
#     )

#     # ── Experience ────────────────────────────────────────
#     experience = (
#         validate_llm_experience(llm.get("experience", []))
#         or parse_experience_section(sections.get("experience", []))
#     )

#     # ── Education ─────────────────────────────────────────
#     education = (
#         llm.get("education")
#         if isinstance(llm.get("education"), list)
#         else parse_education_section(sections.get("education", []))
#     )

#     # ── PROJECTS (CRASH‑PROOF) ────────────────────────────
#     projects = []
#     llm_projects = llm.get("projects")

#     if (
#         isinstance(llm_projects, list)
#         and llm_projects
#         and all(isinstance(p, dict) for p in llm_projects)
#     ):
#         for p in llm_projects:
#             name = str(p.get("name", "") or "").strip()

#             desc = p.get("description", [])
#             if isinstance(desc, str):
#                 desc = [desc]
#             elif isinstance(desc, list):
#                 desc = [str(d).strip() for d in desc if str(d).strip()]
#             else:
#                 desc = []

#             tech = [str(t).strip() for t in p.get("tech_stack", []) if str(t).strip()]
#             links_p = [str(l).strip() for l in p.get("links", []) if str(l).strip()]

#             if name or desc:
#                 projects.append({
#                     "name": name,
#                     "description": desc,
#                     "tech_stack": tech,
#                     "links": links_p,
#                 })
#     else:
#         projects = parse_projects_section(
#             sections.get("projects", []),
#             SKILL_VOCABULARY
#         )

#     # ── Certifications & Awards ─────────────────────────
#     certifications = parse_certifications_section(sections.get("certifications", []))
#     awards = [re.sub(r"^[•\-*]\s*", "", l) for l in sections.get("awards", [])]

#     # ── Skills ──────────────────────────────────────────
#     skills = build_unified_skills(
#         regex_skills=regex_skills,
#         llm_skills=llm.get("skills"),
#         full_text=text,
#         soft_skills=soft_skills,
#     )

#     return {
#         "basic_info": basic_info,
#         "summary": summary,
#         "experience": experience,
#         "education": education,
#         "projects": projects,
#         "skills": skills,
#         "domain": domain,
#         "certifications": certifications,
#         "awards": awards,
#         "spoken_languages": sections.get("languages", []),
#         "extraction_method": "hybrid_llm_rule" if llm else "regex_rule",
#     }


# # app/services/extractor.py
# """
# Production Resume Parsing Pipeline (Crash-Proof)

# FIXES APPLIED vs previous version:
#   [1] build_unified_skills — LLM languages (now a dict) was silently dropped; fixed
#   [2] parse_resume — LLM certifications completely ignored; now merged + preferred
#   [3] parse_resume — location priority wrong (LLM > regex); flipped to regex > LLM
#   [4] parse_resume — _preprocess_resume_text NOT applied to regex text; C/C++ still fused
#   [5] split_language_levels — no guard if score_skills returns strings; added safety cast
#   [6] parse_resume — LLM awards ignored; now merged with regex awards
#   [7] parse_resume — LLM domain ignored; now used when confidence >= 60
#   [8] parse_resume — LLM spoken_languages ignored; now preferred over raw section lines
#   [9] build_unified_skills — no coursework cross-check on regex skills; added purge step
# """

# import logging
# import os
# import re
# from typing import Any, Dict, List, Optional, Set

# import fitz
# import docx
# from fastapi import HTTPException

# from app.services.utils import (
#     clean_text,
#     SECTION_HEADERS,
#     is_heading,
#     extract_emails,
#     extract_phones,
#     extract_links,
#     extract_location,
#     extract_name_fallback,
#     parse_experience_section,
#     parse_education_section,
#     parse_projects_section,
#     parse_certifications_section,
#     extract_skills_rule_based,
#     clean_summary,
#     validate_llm_experience,
#     SKILL_VOCABULARY,
#     normalize_skill_name,
#     SKILL_CANONICAL_CATEGORY,
# )

# from app.services.skill_scoring import (
#     classify_domain,
#     score_skills,
#     extract_soft_skills,
# )

# from app.services.ollama_extractor import (
#     extract_with_ollama,
#     _preprocess_resume_text,   # FIX [4]: apply same preprocessing to regex path
# )

# logger = logging.getLogger(__name__)

# # ─────────────────────────────────────────────────────────────────────────────
# # Language classification
# # ─────────────────────────────────────────────────────────────────────────────

# HIGH_LEVEL_LANGUAGES = {
#     "python", "java", "javascript", "typescript", "c#", "f#", "vb.net",
#     "php", "ruby", "go", "kotlin", "swift", "dart", "julia", "scala",
#     "groovy", "objective-c",
#     "r", "matlab", "sas", "stata",
#     "haskell", "erlang", "elixir", "ocaml", "clojure", "lisp", "scheme",
#     "bash", "shell", "sh", "zsh", "ksh", "powershell", "perl", "awk", "tcl",
#     "html", "css", "sass", "scss",
#     "sql", "plsql", "tsql",
#     "fortran", "cobol", "ada", "crystal", "nim", "smalltalk",
# }

# LOW_LEVEL_LANGUAGES = {
#     "assembly", "asm", "machine code",
#     "c", "c++",
#     "rust", "zig", "v",
# }


# # ─────────────────────────────────────────────────────────────────────────────
# # Text extraction
# # ─────────────────────────────────────────────────────────────────────────────

# def extract_text(file_path: str) -> str:
#     ext = os.path.splitext(file_path)[1].lower()
#     try:
#         if ext == ".pdf":
#             with fitz.open(file_path) as doc:
#                 text = "\n".join(
#                     page.get_text("text")
#                     for page in doc
#                     if page.get_text().strip()
#                 )
#         elif ext == ".docx":
#             doc = docx.Document(file_path)
#             text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
#         else:
#             raise HTTPException(400, "Unsupported file type")
#     except Exception as e:
#         raise HTTPException(500, f"Failed to extract text: {e}")

#     text = clean_text(text)
#     if len(text) < 50:
#         raise HTTPException(400, "Unreadable resume content")
#     return text


# # ─────────────────────────────────────────────────────────────────────────────
# # Section splitting
# # ─────────────────────────────────────────────────────────────────────────────

# def split_sections(text: str) -> Dict[str, List[str]]:
#     sections = {k: [] for k in SECTION_HEADERS}
#     sections["summary"] = []
#     current = "summary"

#     for raw in text.splitlines():
#         line = raw.strip()
#         if not line:
#             continue
#         header = is_heading(line)
#         if header:
#             current = header
#             continue
#         sections.setdefault(current, []).append(line)

#     return sections


# # ─────────────────────────────────────────────────────────────────────────────
# # Language level split  [FIX #5: safety cast so strings don't crash .get()]
# # ─────────────────────────────────────────────────────────────────────────────

# def split_language_levels(scored_langs) -> Dict[str, List]:
#     """
#     Split a list of scored language objects into high/low buckets.

#     FIX #5: score_skills may return plain strings in edge cases.
#     Handles both List[Dict] (normal) and List[str] (fallback).
#     """
#     high, low = [], []

#     for lang in scored_langs:
#         # ── Normalise to dict ────────────────────────────────────────────
#         if isinstance(lang, str):
#             lang = {"name": lang, "score": 0}
#         elif not isinstance(lang, dict):
#             continue

#         name = lang.get("name", "")
#         if not isinstance(name, str):
#             name = str(name)

#         bucket = low if name.lower() in LOW_LEVEL_LANGUAGES else high
#         bucket.append(lang)

#     return {"high_level": high, "low_level": low}


# # ─────────────────────────────────────────────────────────────────────────────
# # Helpers
# # ─────────────────────────────────────────────────────────────────────────────

# def _merge_unique_strings(a: List[str], b: List[str]) -> List[str]:
#     """Merge two string lists, deduplicating case-insensitively."""
#     seen: Set[str] = set()
#     out: List[str] = []
#     for x in a + b:
#         k = str(x).strip().lower()
#         if k and k not in seen:
#             seen.add(k)
#             out.append(str(x).strip())
#     return out


# def _collect_education_coursework(education: List[Dict]) -> Set[str]:
#     """
#     Return a lowercase set of all course names found in education[].coursework.
#     Used to purge coursework from skills (FIX #9).
#     """
#     all_cw: Set[str] = set()
#     for edu in education or []:
#         if not isinstance(edu, dict):
#             continue
#         for cw in edu.get("coursework", []) or []:
#             if isinstance(cw, str) and cw.strip():
#                 all_cw.add(cw.strip().lower())
#     return all_cw


# def _purge_coursework_from_skills(
#     merged: Dict[str, List[str]],
#     coursework: Set[str],
# ) -> Dict[str, List[str]]:
#     """
#     Remove any skill whose lowercase name exactly matches a coursework entry.
#     Operates on the pre-score merged dict (plain strings).
#     """
#     if not coursework:
#         return merged
#     return {
#         cat: [s for s in skills if s.lower() not in coursework]
#         for cat, skills in merged.items()
#     }


# # ─────────────────────────────────────────────────────────────────────────────
# # Unified skills builder  [FIX #1 + FIX #9]
# # ─────────────────────────────────────────────────────────────────────────────

# def build_unified_skills(
#     regex_skills: Dict[str, List[str]],
#     llm_skills: Any,
#     full_text: str,
#     soft_skills: List[str],
#     education: Optional[List[Dict]] = None,   # FIX #9: needed for coursework purge
# ) -> Dict:
#     """
#     Build a clean, deduplicated, correctly categorized skills block.

#     Pipeline:
#       1. Collect all (raw_name, suggested_category) from regex + LLM
#          FIX #1: LLM languages may now be {"high_level": [...], "low_level": [...]}
#       2. Normalize every name to its canonical display form
#       3. Apply canonical category overrides (e.g. spaCy→frameworks)
#       4. Deduplicate globally
#       5. FIX #9: purge any skill whose name matches an education coursework entry
#       6. Score and split languages into high/low level
#     """

#     CATEGORIES = ["technical", "languages", "frameworks", "tools"]

#     # ── Step 1: Collect all candidates ───────────────────────────────────
#     candidates: List[tuple] = []

#     for cat in CATEGORIES:
#         for skill in regex_skills.get(cat, []):
#             if skill:
#                 candidates.append((skill, cat))

#     if isinstance(llm_skills, dict):
#         for cat in CATEGORIES:
#             # ── FIX #1: languages is now a dict, not a list ───────────────
#             if cat == "languages":
#                 lang_val = llm_skills.get("languages")
#                 if isinstance(lang_val, dict):
#                     # New schema: {"high_level": [...], "low_level": [...]}
#                     items = (
#                         list(lang_val.get("high_level") or [])
#                         + list(lang_val.get("low_level")  or [])
#                     )
#                 elif isinstance(lang_val, list):
#                     items = lang_val          # Old flat-list fallback
#                 else:
#                     items = []
#             else:
#                 items = llm_skills.get(cat)
#                 if not isinstance(items, list):
#                     continue

#             for item in items:
#                 if isinstance(item, str):
#                     name = item
#                 elif isinstance(item, dict):
#                     name = item.get("name", "")
#                 else:
#                     name = ""
#                 name = str(name).strip()
#                 if name:
#                     candidates.append((name, cat))

#     # ── Step 2 & 3: Normalize + resolve canonical category ───────────────
#     seen: Dict[str, str] = {}
#     resolved: List[tuple] = []

#     for raw_name, suggested_cat in candidates:
#         norm = normalize_skill_name(raw_name)
#         key  = norm.lower()

#         if not key:
#             continue

#         canon_cat = SKILL_CANONICAL_CATEGORY.get(key)
#         final_cat = canon_cat if canon_cat else suggested_cat

#         if final_cat not in CATEGORIES:
#             continue

#         if key in seen:
#             existing_cat = seen[key]
#             if canon_cat and existing_cat != canon_cat:
#                 seen[key] = canon_cat
#                 resolved = [(n, c) for n, c in resolved if n.lower() != key]
#                 resolved.append((norm, canon_cat))
#             continue

#         seen[key] = final_cat
#         resolved.append((norm, final_cat))

#     # ── Step 4: Build merged dict ─────────────────────────────────────────
#     merged: Dict[str, List[str]] = {cat: [] for cat in CATEGORIES}
#     for norm_name, cat in resolved:
#         merged[cat].append(norm_name)

#     # ── Step 5: Purge coursework from all skill categories  [FIX #9] ─────
#     coursework = _collect_education_coursework(education)
#     merged = _purge_coursework_from_skills(merged, coursework)

#     # ── Step 6: Score ─────────────────────────────────────────────────────
#     scored = score_skills(merged, full_text)

#     return {
#         "technical":   scored.get("technical",  []),
#         "languages":   split_language_levels(scored.get("languages", [])),
#         "frameworks":  scored.get("frameworks", []),
#         "tools":       scored.get("tools",      []),
#         "soft_skills": sorted(set(soft_skills)),
#     }


# # ─────────────────────────────────────────────────────────────────────────────
# # Certification merge helper  [FIX #2]
# # ─────────────────────────────────────────────────────────────────────────────

# def _merge_certifications(
#     llm_certs: List[Dict],
#     regex_certs: List[Dict],
# ) -> List[Dict]:
#     """
#     Prefer LLM certifications (already sanitized by ollama_extractor).
#     Append regex certs that are NOT already covered by the LLM set.
#     Deduplication is name-based, case-insensitive.
#     """
#     merged: List[Dict] = []
#     seen_names: Set[str] = set()

#     for cert in llm_certs:
#         name = str(cert.get("name", "") or "").strip()
#         key  = name.lower()
#         if key and key not in seen_names:
#             seen_names.add(key)
#             merged.append(cert)

#     for cert in regex_certs:
#         name = str(cert.get("name", "") or "").strip()
#         key  = name.lower()
#         if key and key not in seen_names:
#             seen_names.add(key)
#             merged.append(cert)

#     return merged


# # ─────────────────────────────────────────────────────────────────────────────
# # Main pipeline
# # ─────────────────────────────────────────────────────────────────────────────

# def parse_resume(file_path: str) -> Dict:
#     # ── 1. Extract raw text ───────────────────────────────────────────────
#     raw_text = extract_text(file_path)

#     # ── 2. Pre-process BEFORE regex  [FIX #4] ────────────────────────────
#     # _preprocess_resume_text splits "C/C++" → "C, C++" (and similar fused
#     # tokens) so the SAME normalisation applies to BOTH regex AND LLM paths.
#     text = _preprocess_resume_text(raw_text)

#     # ── 3. Section split + regex extraction ──────────────────────────────
#     sections     = split_sections(text)
#     name         = extract_name_fallback(text) or ""
#     emails       = extract_emails(text)
#     phones       = extract_phones(text)
#     links        = extract_links(text)
#     location     = extract_location(text)      # regex-derived; reliable
#     regex_skills = extract_skills_rule_based(text)
#     soft_skills  = extract_soft_skills(text)

#     # ── 4. LLM extraction (safe — never raises) ───────────────────────────
#     # Note: extract_with_ollama calls _preprocess_resume_text internally,
#     # so passing the already-preprocessed text is fine (idempotent).
#     try:
#         llm = extract_with_ollama(text) or {}
#     except Exception:
#         llm = {}

#     llm_basic = llm.get("basic_info", {}) if isinstance(llm, dict) else {}

#     # ── 5. Contact info merge ──────────────────────────────────────────────
#     # FIX #3: Regex location wins — it reads the actual text; LLM is fallback.
#     # (LLM location was already sanitized to None if it looked hallucinated.)
#     basic_info = {
#         "name":     llm_basic.get("name") or name,
#         "emails":   _merge_unique_strings(emails, llm_basic.get("emails", [])),
#         "phones":   _merge_unique_strings(phones, llm_basic.get("phones", [])),
#         "links":    _merge_unique_strings(links,  llm_basic.get("links",  [])),
#         "location": location or llm_basic.get("location"),   # FIX #3
#     }

#     # ── 6. Summary ────────────────────────────────────────────────────────
#     summary = (
#         clean_summary(llm.get("summary"))
#         if isinstance(llm.get("summary"), str)
#         else clean_summary(" ".join(sections.get("summary", [])))
#     )

#     # ── 7. Experience ─────────────────────────────────────────────────────
#     experience = (
#         validate_llm_experience(llm.get("experience", []))
#         or parse_experience_section(sections.get("experience", []))
#     )

#     # ── 8. Education ──────────────────────────────────────────────────────
#     education = (
#         llm.get("education")
#         if isinstance(llm.get("education"), list)
#         else parse_education_section(sections.get("education", []))
#     )

#     # ── 9. Projects (crash-proof) ──────────────────────────────────────────
#     projects: List[Dict] = []
#     llm_projects = llm.get("projects")

#     if (
#         isinstance(llm_projects, list)
#         and llm_projects
#         and all(isinstance(p, dict) for p in llm_projects)
#     ):
#         for p in llm_projects:
#             p_name = str(p.get("name", "") or "").strip()

#             desc = p.get("description", [])
#             if isinstance(desc, str):
#                 desc = [desc]
#             elif isinstance(desc, list):
#                 desc = [str(d).strip() for d in desc if str(d).strip()]
#             else:
#                 desc = []

#             tech    = [str(t).strip() for t in p.get("tech_stack", []) if str(t).strip()]
#             links_p = [str(l).strip() for l in p.get("links",      []) if str(l).strip()]

#             if p_name or desc:
#                 projects.append({
#                     "name":        p_name,
#                     "description": desc,
#                     "tech_stack":  tech,
#                     "links":       links_p,
#                 })
#     else:
#         projects = parse_projects_section(
#             sections.get("projects", []),
#             SKILL_VOCABULARY,
#         )

#     # ── 10. Certifications  [FIX #2] ──────────────────────────────────────
#     # LLM certifications are sanitized (strict keyword + issuer gate).
#     # Regex certs fill any gaps. Merge is name-deduplicated.
#     llm_certs   = llm.get("certifications", []) if isinstance(llm, dict) else []
#     regex_certs = parse_certifications_section(sections.get("certifications", []))
#     certifications = _merge_certifications(
#         llm_certs   if isinstance(llm_certs,   list) else [],
#         regex_certs if isinstance(regex_certs, list) else [],
#     )

#     # ── 11. Awards  [FIX #6] ──────────────────────────────────────────────
#     regex_awards = [
#         re.sub(r"^[•\-*]\s*", "", l)
#         for l in sections.get("awards", [])
#     ]
#     llm_awards = llm.get("awards", []) if isinstance(llm, dict) else []
#     awards = _merge_unique_strings(
#         llm_awards   if isinstance(llm_awards,   list) else [],
#         regex_awards,
#     )

#     # ── 12. Skills (normalized + deduplicated + coursework-purged) ─────────
#     # FIX #1: build_unified_skills now handles LLM languages as a dict.
#     # FIX #9: education passed so coursework can be cross-checked.
#     skills = build_unified_skills(
#         regex_skills=regex_skills,
#         llm_skills=llm.get("skills"),
#         full_text=text,
#         soft_skills=soft_skills,
#         education=education,        # FIX #9
#     )

#     # ── 13. Domain  [FIX #7] ──────────────────────────────────────────────
#     # Use regex classifier as the baseline, then prefer LLM domain when its
#     # confidence is high enough (≥ 60) — LLM sees the whole resume at once.
#     domain = classify_domain(sections, text)
#     llm_domain = llm.get("domain") if isinstance(llm, dict) else None
#     if (
#         isinstance(llm_domain, dict)
#         and isinstance(llm_domain.get("confidence"), (int, float))
#         and llm_domain["confidence"] >= 60
#         and llm_domain.get("name")
#     ):
#         domain = llm_domain         # FIX #7

#     # ── 14. Spoken languages  [FIX #8] ────────────────────────────────────
#     # LLM spoken_languages are structured ("English (Fluent)") vs raw section
#     # lines which may include header noise.  Prefer LLM; fall back to regex.
#     llm_spoken = llm.get("spoken_languages", []) if isinstance(llm, dict) else []
#     if isinstance(llm_spoken, list) and llm_spoken:
#         spoken_languages = [
#             str(s).strip() for s in llm_spoken if str(s).strip()
#         ]
#     else:
#         spoken_languages = [
#             line for line in sections.get("languages", [])
#             if line.strip()
#         ]

#     return {
#         "basic_info":        basic_info,
#         "summary":           summary,
#         "experience":        experience,
#         "education":         education,
#         "projects":          projects,
#         "skills":            skills,
#         "domain":            domain,
#         "certifications":    certifications,
#         "awards":            awards,
#         "spoken_languages":  spoken_languages,
#         "extraction_method": "hybrid_llm_rule" if llm else "regex_rule",
#     }




# app/services/extractor.py
"""
Production Resume Parsing Pipeline (Crash-Proof)

IMPROVEMENTS APPLIED:
  [1] build_unified_skills — LLM languages (now a dict) properly handled
  [2] parse_resume — LLM certifications merged with regex, LLM preferred
  [3] parse_resume — location: regex > LLM with validation
  [4] parse_resume — _preprocess_resume_text applied to regex text
  [5] split_language_levels — safety cast for string inputs
  [6] parse_resume — LLM awards merged with regex awards
  [7] parse_resume — LLM domain used when confidence >= 70 (raised from 60)
  [8] parse_resume — LLM spoken_languages preferred with validation
  [9] build_unified_skills — coursework cross-check purge
  [10] Spoken languages: dedicated extraction with proficiency parsing
  [11] Certifications: strict validation to prevent soft skill inclusion
  [12] Location: improved regex extraction with known city/country validation
"""

import logging
import os
import re
from typing import Any, Dict, List, Optional, Set

import fitz
import docx
from fastapi import HTTPException

from app.services.utils import (
    clean_text,
    SECTION_HEADERS,
    is_heading,
    extract_emails,
    extract_phones,
    extract_links,
    extract_location,
    extract_name_fallback,
    parse_experience_section,
    parse_education_section,
    parse_projects_section,
    parse_certifications_section,
    extract_skills_rule_based,
    clean_summary,
    validate_llm_experience,
    SKILL_VOCABULARY,
    normalize_skill_name,
    SKILL_CANONICAL_CATEGORY,
)

from app.services.skill_scoring import (
    classify_domain,
    score_skills,
    extract_soft_skills,
)

from app.services.ollama_extractor import (
    extract_with_ollama,
    _preprocess_resume_text,
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Language classification
# ─────────────────────────────────────────────────────────────────────────────

HIGH_LEVEL_LANGUAGES = {
    "python", "java", "javascript", "typescript", "c#", "f#", "vb.net",
    "php", "ruby", "go", "kotlin", "swift", "dart", "julia", "scala",
    "groovy", "objective-c",
    "r", "matlab", "sas", "stata",
    "haskell", "erlang", "elixir", "ocaml", "clojure", "lisp", "scheme",
    "bash", "shell", "sh", "zsh", "ksh", "powershell", "perl", "awk", "tcl",
    "html", "css", "sass", "scss",
    "sql", "plsql", "tsql",
    "fortran", "cobol", "ada", "crystal", "nim", "smalltalk",
}

LOW_LEVEL_LANGUAGES = {
    "assembly", "asm", "machine code",
    "c", "c++",
    "rust", "zig", "v",
}


# ─────────────────────────────────────────────────────────────────────────────
# Text extraction
# ─────────────────────────────────────────────────────────────────────────────

def extract_text(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext == ".pdf":
            with fitz.open(file_path) as doc:
                text = "\n".join(
                    page.get_text("text")
                    for page in doc
                    if page.get_text().strip()
                )
        elif ext == ".docx":
            document = docx.Document(file_path)
            text = "\n".join(p.text for p in document.paragraphs if p.text.strip())
        else:
            raise HTTPException(400, "Unsupported file type")
    except Exception as e:
        raise HTTPException(500, f"Failed to extract text: {e}")

    text = clean_text(text)
    if len(text) < 50:
        raise HTTPException(400, "Unreadable resume content")
    return text


# ─────────────────────────────────────────────────────────────────────────────
# Section splitting
# ─────────────────────────────────────────────────────────────────────────────

def split_sections(text: str) -> Dict[str, List[str]]:
    sections = {k: [] for k in SECTION_HEADERS}
    sections["summary"] = []
    current = "summary"

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        header = is_heading(line)
        if header:
            current = header
            continue
        sections.setdefault(current, []).append(line)

    return sections


# ─────────────────────────────────────────────────────────────────────────────
# Language level split
# ─────────────────────────────────────────────────────────────────────────────

def split_language_levels(scored_langs) -> Dict[str, List]:
    """
    Split a list of scored language objects into high/low buckets.
    Handles both List[Dict] (normal) and List[str] (fallback).
    """
    high, low = [], []

    for lang in scored_langs:
        # Normalise to dict
        if isinstance(lang, str):
            lang = {"name": lang, "score": 0}
        elif not isinstance(lang, dict):
            continue

        name = lang.get("name", "")
        if not isinstance(name, str):
            name = str(name)

        bucket = low if name.lower() in LOW_LEVEL_LANGUAGES else high
        bucket.append(lang)

    return {"high_level": high, "low_level": low}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _merge_unique_strings(a: List[str], b: List[str]) -> List[str]:
    """Merge two string lists, deduplicating case-insensitively."""
    seen: Set[str] = set()
    out: List[str] = []
    for x in a + b:
        k = str(x).strip().lower()
        if k and k not in seen:
            seen.add(k)
            out.append(str(x).strip())
    return out


def _collect_education_coursework(education: List[Dict]) -> Set[str]:
    """
    Return a lowercase set of all course names found in education[].coursework.
    """
    all_cw: Set[str] = set()
    for edu in education or []:
        if not isinstance(edu, dict):
            continue
        for cw in edu.get("coursework", []) or []:
            if isinstance(cw, str) and cw.strip():
                all_cw.add(cw.strip().lower())
    return all_cw


def _purge_coursework_from_skills(
    merged: Dict[str, List[str]],
    coursework: Set[str],
) -> Dict[str, List[str]]:
    """
    Remove any skill whose lowercase name exactly matches a coursework entry.
    """
    if not coursework:
        return merged
    return {
        cat: [s for s in skills if s.lower() not in coursework]
        for cat, skills in merged.items()
    }


# ─────────────────────────────────────────────────────────────────────────────
# Spoken language extraction helper
# ─────────────────────────────────────────────────────────────────────────────

# Valid spoken languages
_VALID_SPOKEN_LANGS = {
    "english", "urdu", "hindi", "spanish", "french", "german", "chinese",
    "arabic", "bengali", "russian", "portuguese", "japanese", "punjabi",
    "sindhi", "pashto", "balochi", "korean", "italian", "turkish",
    "vietnamese", "polish", "ukrainian", "romanian", "dutch", "greek",
    "czech", "swedish", "hungarian", "finnish", "norwegian", "danish",
    "hebrew", "thai", "indonesian", "malay", "tagalog", "tamil", "telugu",
    "marathi", "gujarati", "kannada", "malayalam", "odia", "assamese",
    "nepali", "sinhala", "burmese", "khmer", "lao", "mongolian", "persian",
    "farsi", "dari", "kurdish", "uzbek", "kazakh", "tajik", "turkmen",
    "kyrgyz", "azerbaijani", "armenian", "georgian", "albanian", "bosnian",
    "serbian", "croatian", "slovenian", "macedonian", "bulgarian", "slovak",
    "lithuanian", "latvian", "estonian", "belarusian", "moldovan", "irish",
    "scottish", "welsh", "catalan", "basque", "galician", "breton",
    "swahili", "hausa", "yoruba", "igbo", "amharic", "somali", "oromo",
    "zulu", "xhosa", "afrikaans", "shona", "kinyarwanda", "kirundi",
}

# Programming languages to exclude
_PROG_LANGS = {
    "python", "javascript", "typescript", "java", "c", "c++", "c#", "ruby",
    "php", "swift", "kotlin", "go", "scala", "r", "matlab", "dart", "lua",
    "perl", "haskell", "elixir", "erlang", "groovy", "visual basic",
    "cobol", "fortran", "bash", "shell", "sh", "zsh", "ksh", "powershell",
    "julia", "objective-c", "f#", "vb.net", "html", "css", "sass", "scss",
    "sql", "plsql", "tsql", "assembly", "asm", "verilog", "vhdl", "forth",
    "zig", "rust", "crystal", "nim", "smalltalk", "clojure", "lisp",
    "scheme", "awk", "tcl", "sas", "stata", "solidity", "vba", "abap",
}

_PROFICIENCY_PATTERN = re.compile(
    r"\s*\((native|fluent|proficient|intermediate|beginner|basic|"
    r"elementary|pre-intermediate|upper-intermediate|advanced|"
    r"conversational|working|professional|limited|mother\s?tongue)\)",
    re.IGNORECASE,
)


def _extract_spoken_languages_regex(text: str) -> List[str]:
    """
    Extract spoken languages from text using regex patterns.
    Looks for language section content and validates against known languages.
    """
    sections = split_sections(text)
    lang_lines = sections.get("languages", [])

    if not lang_lines:
        return []

    results = []
    seen = set()

    for line in lang_lines:
        line = line.strip()
        if not line:
            continue

        # Remove bullet markers
        line = re.sub(r"^[\d]+[.)]\s*", "", line)
        line = re.sub(r"^[\u2022\-\*\u25e6\u25aa\u25cf]\s*", "", line)

        # Split by common separators
        parts = re.split(r"[,;|]", line)

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Extract language name (remove proficiency in parentheses)
            lang_match = re.match(r"^([^(]+)", part)
            if not lang_match:
                continue
            lang_name = lang_match.group(1).strip().lower()

            # Skip programming languages
            if lang_name in _PROG_LANGS:
                continue

            # Skip if not a valid spoken language
            if lang_name not in _VALID_SPOKEN_LANGS:
                # Check if it contains a valid language as substring
                found_valid = False
                for valid in _VALID_SPOKEN_LANGS:
                    if valid in lang_name or lang_name in valid:
                        found_valid = True
                        lang_name = valid
                        break
                if not found_valid:
                    continue

            # Deduplicate
            if lang_name in seen:
                continue
            seen.add(lang_name)

            # Extract proficiency if present
            prof_match = _PROFICIENCY_PATTERN.search(part)
            if prof_match:
                prof = prof_match.group(1).title()
                display_name = lang_name.title()
                results.append(f"{display_name} ({prof})")
            else:
                results.append(lang_name.title())

    return results


# ─────────────────────────────────────────────────────────────────────────────
# Unified skills builder
# ─────────────────────────────────────────────────────────────────────────────

def build_unified_skills(
    regex_skills: Dict[str, List[str]],
    llm_skills: Any,
    full_text: str,
    soft_skills: List[str],
    education: Optional[List[Dict]] = None,
) -> Dict:
    """
    Build a clean, deduplicated, correctly categorized skills block.
    """

    CATEGORIES = ["technical", "languages", "frameworks", "tools"]

    # Step 1: Collect all candidates
    candidates: List[tuple] = []

    for cat in CATEGORIES:
        for skill in regex_skills.get(cat, []):
            if skill:
                candidates.append((skill, cat))

    if isinstance(llm_skills, dict):
        for cat in CATEGORIES:
            if cat == "languages":
                lang_val = llm_skills.get("languages")
                if isinstance(lang_val, dict):
                    items = (
                        list(lang_val.get("high_level") or [])
                        + list(lang_val.get("low_level")  or [])
                    )
                elif isinstance(lang_val, list):
                    items = lang_val
                else:
                    items = []
            else:
                items = llm_skills.get(cat)
                if not isinstance(items, list):
                    continue

            for item in items:
                if isinstance(item, str):
                    name = item
                elif isinstance(item, dict):
                    name = item.get("name", "")
                else:
                    name = ""
                name = str(name).strip()
                if name:
                    candidates.append((name, cat))

    # Step 2 & 3: Normalize + resolve canonical category
    seen: Dict[str, str] = {}
    resolved: List[tuple] = []

    for raw_name, suggested_cat in candidates:
        norm = normalize_skill_name(raw_name)
        key  = norm.lower()

        if not key:
            continue

        canon_cat = SKILL_CANONICAL_CATEGORY.get(key)
        final_cat = canon_cat if canon_cat else suggested_cat

        if final_cat not in CATEGORIES:
            continue

        if key in seen:
            existing_cat = seen[key]
            if canon_cat and existing_cat != canon_cat:
                seen[key] = canon_cat
                resolved = [(n, c) for n, c in resolved if n.lower() != key]
                resolved.append((norm, canon_cat))
            continue

        seen[key] = final_cat
        resolved.append((norm, final_cat))

    # Step 4: Build merged dict
    merged: Dict[str, List[str]] = {cat: [] for cat in CATEGORIES}
    for norm_name, cat in resolved:
        merged[cat].append(norm_name)

    # Step 5: Purge coursework from all skill categories
    coursework = _collect_education_coursework(education)
    merged = _purge_coursework_from_skills(merged, coursework)

    # Step 6: Score
    scored = score_skills(merged, full_text)

    return {
        "technical":   scored.get("technical",  []),
        "languages":   split_language_levels(scored.get("languages", [])),
        "frameworks":  scored.get("frameworks", []),
        "tools":       scored.get("tools",      []),
        "soft_skills": sorted(set(soft_skills)),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Certification merge helper
# ─────────────────────────────────────────────────────────────────────────────

def _merge_certifications(
    llm_certs: List[Dict],
    regex_certs: List[Dict],
) -> List[Dict]:
    """
    Prefer LLM certifications (already sanitized by ollama_extractor).
    Append regex certs that are NOT already covered by the LLM set.
    Deduplication is name-based, case-insensitive.
    """
    merged: List[Dict] = []
    seen_names: Set[str] = set()

    for cert in llm_certs:
        name = str(cert.get("name", "") or "").strip()
        key  = name.lower()
        if key and key not in seen_names:
            seen_names.add(key)
            merged.append(cert)

    for cert in regex_certs:
        name = str(cert.get("name", "") or "").strip()
        key  = name.lower()
        if key and key not in seen_names:
            seen_names.add(key)
            merged.append(cert)

    return merged


# ─────────────────────────────────────────────────────────────────────────────
# Main pipeline
# ─────────────────────────────────────────────────────────────────────────────

def parse_resume(file_path: str) -> Dict:
    # 1. Extract raw text
    raw_text = extract_text(file_path)

    # 2. Pre-process BEFORE regex
    text = _preprocess_resume_text(raw_text)

    # 3. Section split + regex extraction
    sections     = split_sections(text)
    name         = extract_name_fallback(text) or ""
    emails       = extract_emails(text)
    phones       = extract_phones(text)
    links        = extract_links(text)
    location     = extract_location(text)
    regex_skills = extract_skills_rule_based(text)
    soft_skills  = extract_soft_skills(text)

    # 4. LLM extraction (safe — never raises)
    try:
        llm = extract_with_ollama(text) or {}
    except Exception:
        llm = {}

    llm_basic = llm.get("basic_info", {}) if isinstance(llm, dict) else {}

    # 5. Contact info merge
    # Regex location wins — it reads the actual text; LLM is fallback.
    basic_info = {
        "name":     llm_basic.get("name") or name,
        "emails":   _merge_unique_strings(emails, llm_basic.get("emails", [])),
        "phones":   _merge_unique_strings(phones, llm_basic.get("phones", [])),
        "links":    _merge_unique_strings(links,  llm_basic.get("links",  [])),
        "location": location or llm_basic.get("location"),
    }

    # 6. Summary
    summary = (
        clean_summary(llm.get("summary"))
        if isinstance(llm.get("summary"), str)
        else clean_summary(" ".join(sections.get("summary", [])))
    )

    # 7. Experience
    experience = (
        validate_llm_experience(llm.get("experience", []))
        or parse_experience_section(sections.get("experience", []))
    )

    # 8. Education
    education = (
        llm.get("education")
        if isinstance(llm.get("education"), list)
        else parse_education_section(sections.get("education", []))
    )

    # 9. Projects (crash-proof)
    projects: List[Dict] = []
    llm_projects = llm.get("projects")

    if (
        isinstance(llm_projects, list)
        and llm_projects
        and all(isinstance(p, dict) for p in llm_projects)
    ):
        for p in llm_projects:
            p_name = str(p.get("name", "") or "").strip()

            desc = p.get("description", [])
            if isinstance(desc, str):
                desc = [desc]
            elif isinstance(desc, list):
                desc = [str(d).strip() for d in desc if str(d).strip()]
            else:
                desc = []

            tech    = [str(t).strip() for t in p.get("tech_stack", []) if str(t).strip()]
            links_p = [str(l).strip() for l in p.get("links",      []) if str(l).strip()]

            if p_name or desc:
                projects.append({
                    "name":        p_name,
                    "description": desc,
                    "tech_stack":  tech,
                    "links":       links_p,
                })
    else:
        projects = parse_projects_section(
            sections.get("projects", []),
            SKILL_VOCABULARY,
        )

    # 10. Certifications
    llm_certs   = llm.get("certifications", []) if isinstance(llm, dict) else []
    regex_certs = parse_certifications_section(sections.get("certifications", []))
    certifications = _merge_certifications(
        llm_certs   if isinstance(llm_certs,   list) else [],
        regex_certs if isinstance(regex_certs, list) else [],
    )

    # 11. Awards
    regex_awards = [
        re.sub(r"^[\u2022\-\*]\s*", "", l)
        for l in sections.get("awards", [])
    ]
    llm_awards = llm.get("awards", []) if isinstance(llm, dict) else []
    awards = _merge_unique_strings(
        llm_awards   if isinstance(llm_awards,   list) else [],
        regex_awards,
    )

    # 12. Skills (normalized + deduplicated + coursework-purged)
    skills = build_unified_skills(
        regex_skills=regex_skills,
        llm_skills=llm.get("skills"),
        full_text=text,
        soft_skills=soft_skills,
        education=education,
    )

    # 13. Domain
    # Use regex classifier as the baseline, then prefer LLM domain when its
    # confidence is high enough (>= 70) — LLM sees the whole resume at once.
    domain = classify_domain(sections, text)
    llm_domain = llm.get("domain") if isinstance(llm, dict) else None
    if (
        isinstance(llm_domain, dict)
        and isinstance(llm_domain.get("confidence"), (int, float))
        and llm_domain["confidence"] >= 70
        and llm_domain.get("name")
    ):
        domain = llm_domain

    # 14. Spoken languages
    # Prefer LLM spoken_languages; fall back to regex extraction with validation
    llm_spoken = llm.get("spoken_languages", []) if isinstance(llm, dict) else []
    if isinstance(llm_spoken, list) and llm_spoken:
        spoken_languages = [
            str(s).strip() for s in llm_spoken if str(s).strip()
        ]
    else:
        spoken_languages = _extract_spoken_languages_regex(text)

    return {
        "basic_info":        basic_info,
        "summary":           summary,
        "experience":        experience,
        "education":         education,
        "projects":          projects,
        "skills":            skills,
        "domain":            domain,
        "certifications":    certifications,
        "awards":            awards,
        "spoken_languages":  spoken_languages,
        "extraction_method": "hybrid_llm_rule" if llm else "regex_rule",
    }
