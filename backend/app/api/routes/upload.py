

# # app/api/routes/upload.py
# """
# Resume upload, retrieval, listing, and deletion endpoints.

# POST   /api/resume/upload       — Parse and store a resume
# GET    /api/resume/list         — List all stored resumes (paginated)
# GET    /api/resume/{id}         — Retrieve a single resume
# DELETE /api/resume/{id}         — Delete a resume

# Output contract — every field matches the frontend TypeScript types exactly:
#   basic_info   : { name, emails, phones, location, linkedin, github, links }
#   education    : [{ institution, degree, dates, gpa }]
#   experience   : [{ title, company, dates, bullets }]
#   projects     : [{ title, description, level, tech_tags }]
#   hard_skills  : { skillName: { score, level } }
#   skills_by_category : { category: [name, ...] }
#   skills_structured  : { programming_languages, databases, frameworks, tools_technologies, other }
#   soft_skills  : [str]
#   domain       : { domain, confidence, breakdown }
#   certifications: [str]
#   awards       : [str]
# """

# import logging
# import os
# import re
# from typing import Any, Dict, List, Optional

# from fastapi import APIRouter, File, HTTPException, Query, UploadFile # type: ignore
# from fastapi.responses import JSONResponse # type: ignore

# from app.services.database import (
#     count_resumes,
#     delete_resume,
#     get_resume_by_id,
#     list_resumes,
#     save_resume,
# )
# from app.services.extractor import parse_resume
# from app.services.file_handler import save_file

# logger = logging.getLogger(__name__)
# router = APIRouter(tags=["Resume"])

# _STOP_WORDS = {"and", "or", "the", "&", "also", "–", "—", "-"}

# # ─────────────────────────────────────────────────────────────
# # Response helpers
# # ─────────────────────────────────────────────────────────────

# def _success(data: Dict, status: int = 200) -> JSONResponse:
#     return JSONResponse(status_code=status, content={"success": True, **data})


# def _error(msg: str, status: int = 400) -> JSONResponse:
#     return JSONResponse(status_code=status, content={"success": False, "error": msg})


# # ─────────────────────────────────────────────────────────────
# # Skill constants for structured taxonomy
# # ─────────────────────────────────────────────────────────────

# _HIGH_LEVEL_LANGS = {
#     "python", "javascript", "typescript", "java", "kotlin", "swift",
#     "ruby", "php", "go", "dart", "r", "matlab", "scala", "groovy",
#     "lua", "perl", "sql", "bash", "shell", "html", "css", "sass",
#     "scss", "solidity", "haskell", "elixir", "clojure",
# }

# _LOW_LEVEL_LANGS = {
#     "c", "c++", "c#", "rust", "assembly", "verilog", "vhdl",
#     "fortran", "ada", "cobol", "zig",
# }

# _DB_TOOLS = {
#     "mongodb", "postgresql", "mysql", "redis", "sqlite", "elasticsearch",
#     "cassandra", "dynamodb", "oracle", "mssql", "supabase", "firebase",
#     "mariadb", "couchdb", "neo4j", "influxdb", "bigquery", "snowflake",
#     "databricks", "cockroachdb",
# }

# _ADVANCED_TECH = {
#     "kubernetes", "tensorflow", "pytorch", "aws", "docker", "spark",
#     "kafka", "microservices", "distributed systems", "machine learning",
#     "deep learning", "computer vision", "natural language processing",
# }


# # ─────────────────────────────────────────────────────────────
# # Helpers
# # ─────────────────────────────────────────────────────────────

# def _clean_list(items: List[Any]) -> List[str]:
#     """Remove bullet prefixes and stop words from list items."""
#     result = []
#     for raw in items:
#         val = re.sub(r"^[•\-\*◦▪]\s*", "", str(raw)).strip()
#         if val and val.lower() not in _STOP_WORDS and len(val) > 2:
#             result.append(val)
#     return result


# def _conf_to_level(conf: int) -> str:
#     if conf >= 65:
#         return "advanced"
#     if conf >= 35:
#         return "intermediate"
#     return "beginner"


# # ─────────────────────────────────────────────────────────────
# # Education → { institution, degree, dates, gpa }
# # ─────────────────────────────────────────────────────────────

# def _sanitize_education(edu_list: Any) -> List[Dict]:
#     if not isinstance(edu_list, list):
#         return []
#     result = []
#     for item in edu_list:
#         if isinstance(item, dict):
#             degree = str(item.get("degree", "") or "").strip()
#             field  = str(item.get("field",  "") or "").strip()
#             if field and field.lower() not in degree.lower():
#                 degree_full = f"{degree} in {field}".strip(" in") if degree else field
#             else:
#                 degree_full = degree
#             result.append({
#                 "institution": str(item.get("institution", "") or "").strip(),
#                 "degree":      degree_full,
#                 "dates":       str(item.get("duration", "") or item.get("dates", "") or "").strip(),
#                 "gpa":         item.get("gpa"),
#             })
#         elif isinstance(item, str) and item.strip():
#             result.append({"institution": item.strip(), "degree": "", "dates": "", "gpa": None})
#     return result


# # ─────────────────────────────────────────────────────────────
# # Experience → { title, company, dates, bullets }
# # ─────────────────────────────────────────────────────────────

# def _sanitize_experience(exp_list: Any) -> List[Dict]:
#     if not isinstance(exp_list, list):
#         return []
#     result = []
#     for item in exp_list:
#         if not isinstance(item, dict):
#             continue
#         role    = str(item.get("role",    "") or "").strip()
#         company = str(item.get("company", "") or "").strip()
#         if not role and not company:
#             continue
#         bullets = [
#             str(r).strip()
#             for r in (item.get("responsibilities") or item.get("bullets") or [])
#             if str(r).strip() and len(str(r).strip()) > 5
#         ]
#         result.append({
#             "title":   role,
#             "company": company,
#             "dates":   str(item.get("duration", "") or item.get("dates", "") or "").strip(),
#             "bullets": bullets,
#         })
#     return result


# # ─────────────────────────────────────────────────────────────
# # Projects → [{ title, description, level, tech_tags }]
# # ─────────────────────────────────────────────────────────────

# def _build_projects(projects_raw: Any) -> List[Dict]:
#     if not isinstance(projects_raw, list):
#         return []
#     result = []
#     for item in projects_raw:
#         if isinstance(item, str) and item.strip():
#             result.append({
#                 "title":       item.strip(),
#                 "description": "",
#                 "level":       "intermediate",
#                 "tech_tags":   [],
#             })
#         elif isinstance(item, dict):
#             name = str(item.get("name", "") or "").strip()
#             desc = item.get("description", "")
#             if isinstance(desc, list):
#                 desc = " ".join(str(d) for d in desc if str(d).strip())
#             desc = str(desc or "").strip()

#             tech_stack = item.get("tech_stack") or []
#             if not isinstance(tech_stack, list):
#                 tech_stack = []
#             tech_tags = [str(t).strip() for t in tech_stack if str(t).strip()]

#             tags_lower = {t.lower() for t in tech_tags}
#             desc_lower = desc.lower()
#             if len(tech_tags) >= 5 or tags_lower & _ADVANCED_TECH or any(t in desc_lower for t in _ADVANCED_TECH):
#                 level = "advanced"
#             elif len(tech_tags) >= 2 or len(desc) > 100:
#                 level = "intermediate"
#             else:
#                 level = "beginner"

#             if name or desc:
#                 result.append({
#                     "title":       name or "Untitled Project",
#                     "description": desc,
#                     "level":       level,
#                     "tech_tags":   tech_tags,
#                 })
#     return result


# # ─────────────────────────────────────────────────────────────
# # Skills → hard_skills + skills_by_category + skills_structured
# # ─────────────────────────────────────────────────────────────

# def _build_skills_frontend(skills_raw: Any) -> Dict:
#     """
#     Transform backend skills dict to the three frontend skill shapes.

#     Input:  { technical, languages, frameworks, tools, other } → [{name, confidence}]
#     Output: { hard_skills, skills_by_category, skills_structured }
#     """
#     if not isinstance(skills_raw, dict):
#         empty_pl: Dict = {}
#         return {
#             "hard_skills": {},
#             "skills_by_category": {},
#             "skills_structured": {
#                 "programming_languages": empty_pl,
#                 "databases": [], "frameworks": [],
#                 "tools_technologies": [], "other": [],
#             },
#         }

#     # Flatten into a single annotated list
#     all_items: List[Dict] = []
#     for cat in ("technical", "languages", "frameworks", "tools", "other"):
#         for item in (skills_raw.get(cat) or []):
#             if isinstance(item, dict) and item.get("name"):
#                 all_items.append({
#                     "name":       item["name"].strip(),
#                     "confidence": int(item.get("confidence", 10)),
#                     "cat":        cat,
#                 })
#             elif isinstance(item, str) and item.strip():
#                 all_items.append({"name": item.strip(), "confidence": 10, "cat": cat})

#     # hard_skills: { name: { score, level } }
#     hard_skills: Dict[str, Dict] = {
#         s["name"]: {
#             "score": s["confidence"],
#             "level": _conf_to_level(s["confidence"]),
#         }
#         for s in all_items
#     }

#     # skills_by_category: { category: [name, ...] }
#     skills_by_category: Dict[str, List[str]] = {}
#     for s in all_items:
#         skills_by_category.setdefault(s["cat"], []).append(s["name"])

#     # skills_structured — split languages and tools into subcategories
#     lang_items = [s for s in all_items if s["cat"] == "languages"]
#     high_level = [s["name"] for s in lang_items if s["name"].lower() in _HIGH_LEVEL_LANGS]
#     low_level  = [s["name"] for s in lang_items if s["name"].lower() in _LOW_LEVEL_LANGS]
#     # Unknown languages → high-level by default
#     other_lang = [
#         s["name"] for s in lang_items
#         if s["name"].lower() not in _HIGH_LEVEL_LANGS
#         and s["name"].lower() not in _LOW_LEVEL_LANGS
#     ]
#     high_level += other_lang

#     tool_items        = [s for s in all_items if s["cat"] == "tools"]
#     databases         = [s["name"] for s in tool_items if s["name"].lower() in _DB_TOOLS]
#     tools_technologies = [s["name"] for s in tool_items if s["name"].lower() not in _DB_TOOLS]

#     frameworks = [s["name"] for s in all_items if s["cat"] == "frameworks"]
#     other_all  = [s["name"] for s in all_items if s["cat"] in ("technical", "other")]

#     pl: Dict = {}
#     if high_level:
#         pl["high_level"] = high_level
#     if low_level:
#         pl["low_level"] = low_level

#     skills_structured = {
#         "programming_languages": pl,
#         "databases":             databases,
#         "frameworks":            frameworks,
#         "tools_technologies":    tools_technologies,
#         "other":                 other_all,
#     }

#     return {
#         "hard_skills":         hard_skills,
#         "skills_by_category":  skills_by_category,
#         "skills_structured":   skills_structured,
#     }


# # ─────────────────────────────────────────────────────────────
# # Certifications → [str]   (structured dict → readable string)
# # ─────────────────────────────────────────────────────────────

# def _build_certifications(certs_raw: Any) -> List[str]:
#     if not isinstance(certs_raw, list):
#         return []
#     result = []
#     for item in certs_raw:
#         if isinstance(item, str) and item.strip():
#             val = re.sub(r"^[•\-\*◦▪]\s*", "", item).strip()
#             if val and len(val) > 2:
#                 result.append(val)
#         elif isinstance(item, dict) and item.get("name"):
#             parts = [item["name"].strip()]
#             if item.get("issuer"):
#                 parts.append(str(item["issuer"]).strip())
#             if item.get("date"):
#                 parts.append(str(item["date"]).strip())
#             result.append(" · ".join(p for p in parts if p))
#     return result


# # ─────────────────────────────────────────────────────────────
# # Main payload assembler
# # ─────────────────────────────────────────────────────────────

# def _assemble_payload(parsed: Dict, filename: str) -> Dict:
#     """
#     Assemble the final frontend-safe payload from parsed resume data.
#     Output shape matches the TypeScript ResumeData interface exactly.
#     """
#     basic = parsed.get("basic_info") or {}

#     # Extract linkedin / github from links list
#     all_links = [str(l).strip() for l in (basic.get("links") or []) if str(l).strip()]
#     linkedin   = next((l for l in all_links if "linkedin" in l.lower()), "")
#     github     = next((l for l in all_links if "github"   in l.lower()), "")
#     other_links = [
#         l for l in all_links
#         if "linkedin" not in l.lower() and "github" not in l.lower()
#     ]

#     # Domain — backend key is "name", frontend expects "domain"
#     domain_raw = parsed.get("domain") or {}
#     domain: Dict = {
#         "domain":     domain_raw.get("name") or domain_raw.get("domain") or None,
#         "confidence": float(domain_raw.get("confidence", 0.0)),
#         "breakdown":  domain_raw.get("breakdown") or {},
#     }

#     # Skills → three frontend shapes
#     skills_built = _build_skills_frontend(parsed.get("skills"))

#     return {
#         "basic_info": {
#             "name":     str(basic.get("name",     "") or "").strip(),
#             "emails":   [str(e).strip() for e in (basic.get("emails") or [])  if str(e).strip()],
#             "phones":   [str(p).strip() for p in (basic.get("phones") or [])  if str(p).strip()],
#             "location": str(basic.get("location", "") or "").strip(),
#             "linkedin": linkedin,
#             "github":   github,
#             "links":    other_links,
#         },
#         "summary":             str(parsed.get("summary", "") or "").strip(),
#         "education":           _sanitize_education(parsed.get("education", [])),
#         "experience":          _sanitize_experience(parsed.get("experience", [])),
#         "projects":            _build_projects(parsed.get("projects", [])),
#         "hard_skills":         skills_built["hard_skills"],
#         "skills_by_category":  skills_built["skills_by_category"],
#         "skills_structured":   skills_built["skills_structured"],
#         "soft_skills": [
#             str(s).strip()
#             for s in (parsed.get("soft_skills") or [])
#             if str(s).strip()
#         ],
#         "domain":              domain,
#         "certifications":      _build_certifications(parsed.get("certifications", [])),
#         "awards":              _clean_list(parsed.get("awards", [])),
#         "extraction_method":   parsed.get("extraction_method", "regex_rule"),
#     }


# # ─────────────────────────────────────────────────────────────
# # POST /upload
# # ─────────────────────────────────────────────────────────────

# @router.post("/upload")
# async def upload_resume(file: UploadFile = File(...)):
#     """Upload a resume PDF or DOCX, parse it, store it, return structured data."""
#     file_path = ""
#     try:
#         filename = file.filename or ""
#         ext = os.path.splitext(filename)[1].lower()
#         if ext not in (".pdf", ".docx"):
#             return _error("Only PDF and DOCX files are supported", 400)

#         file_path = await save_file(file)

#         logger.info("Parsing resume: %s", filename)
#         parsed = parse_resume(file_path)

#         data = _assemble_payload(parsed, filename)

#         resume_id = await save_resume(filename, data)
#         logger.info("Stored resume ID=%s file=%s", resume_id, filename)

#         return _success({"resume_id": resume_id, "file_name": filename, "data": data}, status=201)

#     except HTTPException as exc:
#         logger.warning("HTTP error during upload: %s", exc.detail)
#         return _error(exc.detail, exc.status_code)

#     except Exception as exc:
#         logger.error("Unexpected error during upload", exc_info=True)
#         return _error(f"Processing failed: {exc}", 500)

#     finally:
#         if file_path and os.path.exists(file_path):
#             try:
#                 os.remove(file_path)
#             except OSError:
#                 pass


# # ─────────────────────────────────────────────────────────────
# # GET /list
# # ─────────────────────────────────────────────────────────────

# @router.get("/list")
# async def list_all_resumes(
#     skip:  int = Query(0,  ge=0,          description="Number of records to skip"),
#     limit: int = Query(20, ge=1, le=100,  description="Max records to return"),
# ):
#     """List all stored resumes with pagination."""
#     items = await list_resumes(skip=skip, limit=limit)
#     total = await count_resumes()
#     return _success({"total": total, "skip": skip, "limit": limit, "items": items})


# # ─────────────────────────────────────────────────────────────
# # GET /{resume_id}
# # ─────────────────────────────────────────────────────────────

# @router.get("/{resume_id}")
# async def get_resume(resume_id: str):
#     """Retrieve a single stored resume by ID."""
#     resume = await get_resume_by_id(resume_id)
#     if not resume:
#         return _error("Resume not found", 404)
#     return _success({"resume": resume})


# # ─────────────────────────────────────────────────────────────
# # DELETE /{resume_id}
# # ─────────────────────────────────────────────────────────────

# @router.delete("/{resume_id}")
# async def delete_resume_entry(resume_id: str):
#     """Delete a stored resume by ID."""
#     deleted = await delete_resume(resume_id)
#     if not deleted:
#         return _error("Resume not found", 404)
#     return _success({"message": "Resume deleted successfully"})


#############################################################################################
#############################################################################################


# app/api/routes/upload.py

import logging
import os
from typing import Optional

from fastapi import APIRouter, File, Query, UploadFile
from fastapi.responses import JSONResponse
from app.services.utils import calculate_total_experience


from app.services.database import (
    count_resumes,
    delete_resume,
    get_education_levels,
    get_fields_by_level,
    get_full_tree,
    get_resume_by_id,
    list_resumes,
    list_resumes_by_category,
    list_resumes_by_level,
    save_resume,
    search_resumes,
)
from app.services.extractor import parse_resume
from app.services.file_handler import save_file

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Resume"])


# ─────────────────────────────────────────────
# Response helpers
# ─────────────────────────────────────────────

def _success(data, status=200):
    return JSONResponse({"success": True, **data}, status_code=status)

def _error(msg, status=400):
    return JSONResponse({"success": False, "error": msg}, status_code=status)


# ─────────────────────────────────────────────
# Payload builder
# ─────────────────────────────────────────────

def _assemble(parsed: dict, filename: str) -> dict:
    experience = parsed.get("experience", [])          # ← extract first
    exp_summary = calculate_total_experience(experience)  # ← then compute

    return {
        "file_name":         filename,
        "basic_info":        parsed.get("basic_info",        {}),
        "summary":           parsed.get("summary",           ""),
        "education":         parsed.get("education",         []),
        "experience":        experience,               # ← use the variable
        "total_experience": {
            "years":        exp_summary["total_years"],
            "months":       exp_summary["total_months"],
            "total_months": exp_summary["total_months_raw"],
            "display":      exp_summary["display"],
        },
        "projects":          parsed.get("projects",          []),
        "skills":            parsed.get("skills",            {}),
        "certifications":    parsed.get("certifications",    []),
        "awards":            parsed.get("awards",            []),
        "spoken_languages":  parsed.get("spoken_languages",  []),
        "domain":            parsed.get("domain",            {}),
        "extraction_method": parsed.get("extraction_method", "regex_rule"),
    }

# ─────────────────────────────────────────────
# Upload
# ─────────────────────────────────────────────

@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    file_path = ""
    try:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in (".pdf", ".docx"):
            return _error("Only PDF and DOCX files are supported")

        file_path   = await save_file(file)
        parsed      = parse_resume(file_path)
        if not parsed:
            return _error("Failed to parse resume")

        data        = _assemble(parsed, file.filename)
        save_result = await save_resume(file.filename, data)

        return _success(
            {
                "resume_id":       save_result["resume_id"],
                "education_level": save_result["education_level"],
                "field":           save_result["field"],
                "resume_number":   save_result["resume_number"],
                "file_name":       file.filename,
                "data":            data,
            },
            status=201,
        )

    except Exception as e:
        logger.error("Upload failed", exc_info=True)
        return _error(str(e), status=500)

    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)


# ─────────────────────────────────────────────
# Search Endpoint
# ─────────────────────────────────────────────
@router.get("/search")
async def search(
    level: Optional[str] = Query(None, description="Education level"),
    field: Optional[str] = Query(None, description="Field/domain"),
    keyword: Optional[str] = Query(None, description="Search in name, skills, summary, etc."),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    result = await search_resumes(
        level=level,
        field=field,
        keyword=keyword,
        skip=skip,
        limit=limit,
    )
    return _success(result)


# ─────────────────────────────────────────────
# Tree navigation
# ─────────────────────────────────────────────

@router.get("/tree")
async def get_tree():
    """Full tree: levels → fields → counts."""
    return _success({"tree": await get_full_tree()})


@router.get("/tree/levels")
async def get_levels():
    """All education levels with resume counts."""
    return _success({"levels": await get_education_levels()})


@router.get("/tree/levels/{level}/fields")
async def get_fields(level: str):
    """All fields under a given education level."""
    return _success({"fields": await get_fields_by_level(level)})


@router.get("/tree/levels/{level}/fields/{field}/resumes")
async def get_category_resumes(level: str, field: str):
    """All resumes inside a specific level + field bucket."""
    items = await list_resumes_by_category(level, field)
    return _success({"items": items, "total": len(items)})


@router.get("/tree/levels/{level}/resumes")
async def get_level_resumes(level: str):
    """All resumes under one education level (all fields)."""
    items = await list_resumes_by_level(level)
    return _success({"items": items, "total": len(items)})


# ─────────────────────────────────────────────
# Flat list / single / delete
# ─────────────────────────────────────────────

@router.get("/list")
async def list_all(skip: int = 0, limit: int = 20):
    return _success({
        "items": await list_resumes(skip, limit),
        "total": await count_resumes(),
    })


@router.get("/{resume_id}")
async def get_one(resume_id: str):
    res = await get_resume_by_id(resume_id)
    if not res:
        return _error("Resume not found", 404)
    return _success({"resume": res})


@router.delete("/{resume_id}")
async def delete_one(resume_id: str):
    ok = await delete_resume(resume_id)
    if not ok:
        return _error("Resume not found", 404)
    return _success({"message": "Resume deleted"})