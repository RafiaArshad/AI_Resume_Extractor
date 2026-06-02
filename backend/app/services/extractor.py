# app/services/extractor.py
"""
Production Resume Parsing Pipeline (Crash-Proof)

IMPROVEMENTS APPLIED:
  [1] parse_resume — LLM certifications merged with regex, LLM preferred
  [2] parse_resume — location: regex > LLM with validation
  [3] parse_resume — _preprocess_resume_text applied to regex text
  [4] split_language_levels — safety cast for string inputs
  [5] parse_resume — LLM awards merged with regex awards
  [6] parse_resume — LLM domain used when confidence >= 70 (raised from 60)
  [7] parse_resume — LLM spoken_languages preferred with validation
  [8] build_unified_skills — coursework cross-check purge
  [9] Spoken languages: dedicated extraction with proficiency parsing
  [10] Certifications: strict validation to prevent soft skill inclusion
  [11] Location: improved regex extraction with known city/country validation
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
