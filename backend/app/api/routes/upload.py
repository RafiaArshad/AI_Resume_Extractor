

# # app/api/routes/upload.py
# """
# Resume upload, retrieval, listing, and deletion endpoints.

# POST   /api/resume/upload       — Parse and store a resume
# GET    /api/resume/list         — List all stored resumes (paginated)
# GET    /api/resume/{id}         — Retrieve a single resume
# DELETE /api/resume/{id}         — Delete a resume

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
