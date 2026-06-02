# # app/services/database.py

# import os
# from datetime import datetime, timezone
# from typing import Dict, List, Optional

# from bson import ObjectId
# from bson.errors import InvalidId
# from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

# # ─────────────────────────────────────────────────────────────
# # Configuration
# # ─────────────────────────────────────────────────────────────

# MONGO_URI  = os.getenv("MONGO_URI", "mongodb://localhost:27017")
# DB_NAME    = os.getenv("MONGO_DB",  "ai_resume_db")
# COLLECTION = "resumes"

# _client: Optional[AsyncIOMotorClient] = None
# _db:     Optional[AsyncIOMotorDatabase] = None


# # ─────────────────────────────────────────────────────────────
# # Connection Lifecycle
# # ─────────────────────────────────────────────────────────────

# async def connect_db() -> None:
#     global _client, _db

#     _client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
#     _db = _client[DB_NAME]

#     # Core indexes
#     await _db[COLLECTION].create_index("uploaded_at")
#     await _db[COLLECTION].create_index("updated_at")
#     await _db[COLLECTION].create_index("file_name")
#     await _db[COLLECTION].create_index("basic_info.name")
#     await _db[COLLECTION].create_index("domain.domain")

#     print(f"[DB] Connected → {MONGO_URI}/{DB_NAME}")


# async def close_db() -> None:
#     global _client
#     if _client:
#         _client.close()
#         print("[DB] MongoDB connection closed.")


# def get_db() -> AsyncIOMotorDatabase:
#     if _db is None:
#         raise RuntimeError(
#             "Database not initialized. Call connect_db() on startup."
#         )
#     return _db


# # ─────────────────────────────────────────────────────────────
# # Serialization Helper
# # ─────────────────────────────────────────────────────────────

# def _serialize(obj):
#     if isinstance(obj, dict):
#         return {k: _serialize(v) for k, v in obj.items()}
#     if isinstance(obj, list):
#         return [_serialize(item) for item in obj]
#     if isinstance(obj, ObjectId):
#         return str(obj)
#     if isinstance(obj, datetime):
#         return obj.isoformat()
#     return obj


# # ─────────────────────────────────────────────────────────────
# # Resume Document Builder
# # ─────────────────────────────────────────────────────────────

# def _empty_skills_block() -> Dict:
#     """Return the canonical empty unified skills structure."""
#     return {
#         "languages": {
#             "high_level": [],
#             "low_level":  [],
#         },
#         "libraries_frameworks":   [],
#         "tools_technologies":     [],
#         "ai_ml_specializations":  [],   # GenAI / LLM / ML specific
#         "cloud_devops":           [],   # AWS, GCP, Azure, Docker, K8s …
#         "core_domains":           [],   # Architecture, system design, etc.
#         "fundamentals":           [],   # OOP, data structures, algorithms
#     }


# def _build_resume_doc(file_name: str, data: Dict) -> Dict:
#     now = datetime.now(tz=timezone.utc)

#     return {
#         "file_name":   file_name,
#         "uploaded_at": now,
#         "updated_at":  now,
#         "status":      "processed",

#         # Contact / header
#         "basic_info": data.get("basic_info", {
#             "name": "", "emails": [], "phones": [],
#             "location": "", "linkedin": "", "github": "", "links": [],
#         }),

#         "summary":    data.get("summary", ""),
#         "education":  data.get("education", []),
#         "experience": data.get("experience", []),
#         "projects":   data.get("projects", []),

#         # Primary unified skills block (7 categories)
#         "skills": data.get("skills", _empty_skills_block()),

#         # Legacy compatibility fields
#         "hard_skills":         data.get("hard_skills", {}),
#         "skills_by_category":  data.get("skills_by_category", {
#             "technical": [], "tools": [], "frameworks": [], "languages": [],
#         }),
#         "skills_structured": data.get("skills_structured", {
#             "programming_languages": {"high_level": [], "low_level": []},
#             "databases": [], "frameworks": [], "tools_technologies": [], "other": [],
#         }),

#         "soft_skills": data.get("soft_skills", []),

#         # Domain intelligence
#         "domain": data.get("domain", {
#             "domain":     None,
#             "confidence": 0.0,
#             "breakdown":  {},
#         }),

#         "certifications":    data.get("certifications", []),
#         "awards":            data.get("awards", []),
#         "extraction_method": data.get("extraction_method", "regex_rule"),
#         "raw_text":          data.get("raw_text"),
#     }


# # ─────────────────────────────────────────────────────────────
# # CRUD Operations
# # ─────────────────────────────────────────────────────────────

# async def save_resume(file_name: str, data: Dict) -> str:
#     db  = get_db()
#     doc = _build_resume_doc(file_name, data)
#     result = await db[COLLECTION].insert_one(doc)
#     return str(result.inserted_id)


# async def get_resume_by_id(resume_id: str) -> Optional[Dict]:
#     try:
#         oid = ObjectId(resume_id)
#     except (InvalidId, Exception):
#         return None
#     db  = get_db()
#     doc = await db[COLLECTION].find_one({"_id": oid})
#     return _serialize(doc) if doc else None


# async def list_resumes(skip: int = 0, limit: int = 20) -> List[Dict]:
#     db = get_db()
#     cursor = (
#         db[COLLECTION]
#         .find(
#             {},
#             projection={
#                 "file_name":         1,
#                 "uploaded_at":       1,
#                 "basic_info.name":   1,
#                 "domain.domain":     1,
#                 "domain.confidence": 1,
#                 "extraction_method": 1,
#                 "status":            1,
#             },
#         )
#         .sort("uploaded_at", -1)
#         .skip(skip)
#         .limit(limit)
#     )
#     results = []
#     async for doc in cursor:
#         results.append(_serialize(doc))
#     return results


# async def update_resume(resume_id: str, new_data: Dict) -> bool:
#     try:
#         oid = ObjectId(resume_id)
#     except (InvalidId, Exception):
#         return False
#     db = get_db()
#     result = await db[COLLECTION].update_one(
#         {"_id": oid},
#         {"$set": {**new_data, "updated_at": datetime.now(tz=timezone.utc)}},
#     )
#     return result.modified_count > 0


# async def delete_resume(resume_id: str) -> bool:
#     try:
#         oid = ObjectId(resume_id)
#     except (InvalidId, Exception):
#         return False
#     db = get_db()
#     result = await db[COLLECTION].delete_one({"_id": oid})
#     return result.deleted_count > 0


# async def count_resumes() -> int:
#     db = get_db()
#     return await db[COLLECTION].count_documents({})

# # app/services/database.py
# """
# MongoDB persistence layer for AI Resume Extractor.

# Hierarchy:
#   Education Level (Bachelor / Master / PhD / Unknown)
#     └── Field / Domain  (Computer Engineering, Data Science, …)
#           └── Resume #1, #2, #3 …

# Category document (resume_categories):
#   {
#     "education_level": "Bachelor",
#     "field":           "Computer Engineering",
#     "category_key":    "bachelor::computer engineering",
#     "category_code":   "BCE",          # B + CE
#     "count":           12              # live counter
#   }

# Resume document (resumes) carries:
#   category: {
#     education_level, field, category_key, category_code, resume_number
#   }
# """


# # app/services/database.py
# """
# MongoDB persistence layer — 3-level category tree
# ==================================================

# Level 1  →  education_level   (Bachelor / Master / PhD / Diploma / Other)
# Level 2  →  field             (Computer Engineering, Data Science, …)
# Level 3  →  resume_number     (1, 2, 3 … per field bucket)

# Collections
# -----------
# education_levels   – one doc per unique level
#   { _id, level_name, created_at }

# resume_categories  – one doc per (level × field) pair
#   { _id, education_level_id, education_level, field,
#     category_key, category_code, resume_count, created_at }

# resumes            – one doc per uploaded resume
#   {
#     _id, file_name, uploaded_at, updated_at,
#     category: {
#       education_level_id, education_level,
#       category_id, field, category_key, category_code,
#       resume_number                    ← sequential within the field bucket
#     },
#     basic_info, summary, education, experience, projects,
#     skills, certifications, awards, spoken_languages,
#     domain, extraction_method
#   }

# category_counters  – internal sequential-id store (keyed by category_key)
# """

# import os
# import re
# from datetime import datetime, timezone
# from typing import Any, Dict, List, Optional

# from bson import ObjectId
# from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
# from pymongo import ReturnDocument

# # ─────────────────────────────────────────────────────────────
# # Config
# # ─────────────────────────────────────────────────────────────

# MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
# DB_NAME   = os.getenv("MONGO_DB",  "ai_resume_db")

# COL_RESUMES    = "resumes"
# COL_LEVELS     = "education_levels"
# COL_CATEGORIES = "resume_categories"
# COL_COUNTERS   = "category_counters"

# _client: Optional[AsyncIOMotorClient]   = None
# _db:     Optional[AsyncIOMotorDatabase] = None


# # ─────────────────────────────────────────────────────────────
# # Lifecycle
# # ─────────────────────────────────────────────────────────────

# async def connect_db() -> None:
#     global _client, _db

#     _client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
#     _db     = _client[DB_NAME]

#     # education_levels
#     await _db[COL_LEVELS].create_index("level_name", unique=True)

#     # resume_categories
#     await _db[COL_CATEGORIES].create_index("category_key", unique=True)
#     await _db[COL_CATEGORIES].create_index("education_level")
#     await _db[COL_CATEGORIES].create_index("field")
#     await _db[COL_CATEGORIES].create_index(
#         [("education_level", 1), ("field", 1)]
#     )

#     # resumes
#     r = _db[COL_RESUMES]
#     await r.create_index("uploaded_at")
#     await r.create_index("updated_at")
#     await r.create_index("file_name")
#     await r.create_index("basic_info.name")
#     await r.create_index("category.education_level")
#     await r.create_index("category.field")
#     await r.create_index("category.category_key")
#     await r.create_index("category.resume_number")
#     # NOTE: NO unique index on (category_key, resume_number).
#     # Uniqueness is guaranteed atomically by _next_resume_number().
#     # A unique index here causes DuplicateKeyError when the LLM fails
#     # mid-flight and the counter advances without a successful insert.

#     # Drop the bad index if it still exists from a previous deployment
#     try:
#         await r.drop_index("category.category_key_1_category.resume_number_1")
#     except Exception:
#         pass  # Index didn't exist — fine

#     print(f"[DB] Connected -> {MONGO_URI}/{DB_NAME}")


# async def close_db() -> None:
#     global _client
#     if _client:
#         _client.close()
#         print("[DB] Disconnected.")


# def get_db() -> AsyncIOMotorDatabase:
#     if _db is None:
#         raise RuntimeError("DB not initialised — call connect_db() first.")
#     return _db


# # ─────────────────────────────────────────────────────────────
# # Serialisation
# # ─────────────────────────────────────────────────────────────

# def _serialize(obj: Any) -> Any:
#     if isinstance(obj, dict):
#         return {k: _serialize(v) for k, v in obj.items()}
#     if isinstance(obj, list):
#         return [_serialize(i) for i in obj]
#     if isinstance(obj, ObjectId):
#         return str(obj)
#     if isinstance(obj, datetime):
#         return obj.isoformat()
#     return obj


# # ─────────────────────────────────────────────────────────────
# # Level 1 — Education level inference
# # ─────────────────────────────────────────────────────────────

# _LEVEL_RULES: List[tuple] = [
#     (re.compile(r"\b(ph\.?\s*d|doctor(ate)?)\b",                re.I), "PhD"),
#     (re.compile(r"\b(master|m\.?\s*sc?|m\.?\s*eng?|mba|mpa)\b", re.I), "Master"),
#     (re.compile(
#         r"\b(bachelor|b\.?\s*sc?|b\.?\s*eng?|b\.?\s*s\.?\s*e?"
#         r"|\bbs\b|\bbe\b|\bba\b)\b", re.I), "Bachelor"),
#     (re.compile(r"\b(diploma|associate|a\.?\s*s\.?)\b",          re.I), "Diploma"),
# ]


# def _infer_level(degree_str: str) -> str:
#     if not degree_str:
#         return "Other"
#     for pattern, label in _LEVEL_RULES:
#         if pattern.search(degree_str):
#             return label
#     return "Other"


# def _get_highest_level(education: List[Dict]) -> str:
#     """Return the highest level across all education entries."""
#     rank = {"PhD": 4, "Master": 3, "Bachelor": 2, "Diploma": 1, "Other": 0}
#     best = "Other"
#     for edu in education or []:
#         lvl = _infer_level((edu.get("degree") or "").strip())
#         if rank.get(lvl, 0) > rank.get(best, 0):
#             best = lvl
#     return best


# # ─────────────────────────────────────────────────────────────
# # Level 2 — Field extraction
# # ─────────────────────────────────────────────────────────────

# _DEGREE_PREFIX = re.compile(
#     r"^(bachelor(?:'?s)?(\s+of)?|master(?:'?s)?(\s+of)?|ph\.?\s*d\.?(\s+in)?"
#     r"|b\.?\s*sc?\.?|m\.?\s*sc?\.?|b\.?\s*eng?\.?|m\.?\s*eng?\.?"
#     r"|b\.?\s*s\.?|b\.?\s*a\.?|m\.?\s*a\.?|associate(\s+of)?)\s*",
#     re.I,
# )


# def _extract_field(education: List[Dict], domain: Optional[Dict]) -> str:
#     """
#     Priority:
#       1. education[].field           e.g. "Computer Engineering"
#       2. education[].degree stripped  e.g. "BS Computer Science" -> "Computer Science"
#       3. LLM domain name             snake_case -> Title Case
#       4. "General"
#     """
#     for edu in education or []:
#         f = (edu.get("field") or "").strip()
#         if f:
#             return f.title()

#     for edu in education or []:
#         d = (edu.get("degree") or "").strip()
#         if d:
#             cleaned = _DEGREE_PREFIX.sub("", d).strip()
#             if cleaned:
#                 return cleaned.title()

#     if isinstance(domain, dict):
#         name = (domain.get("name") or "").strip()
#         if name:
#             return name.replace("_", " ").title()

#     return "General"


# # ─────────────────────────────────────────────────────────────
# # Category key & short code
# # ─────────────────────────────────────────────────────────────

# def _category_key(level: str, field: str) -> str:
#     return f"{level.lower()}::{field.lower()}"


# def _category_code(level: str, field: str) -> str:
#     """Bachelor + Computer Engineering -> 'BCE'"""
#     prefix = (level or "X")[0].upper()
#     words  = re.findall(r"[A-Za-z]+", field)
#     suffix = "".join(w[0].upper() for w in words) if words else "GEN"
#     return prefix + suffix


# # ─────────────────────────────────────────────────────────────
# # Upserts (one per collection level)
# # ─────────────────────────────────────────────────────────────

# async def _upsert_education_level(level: str) -> str:
#     """Ensure doc in education_levels. Returns _id string."""
#     db  = get_db()
#     doc = await db[COL_LEVELS].find_one_and_update(
#         {"level_name": level},
#         {"$setOnInsert": {
#             "level_name": level,
#             "created_at": datetime.now(timezone.utc),
#         }},
#         upsert=True,
#         return_document=ReturnDocument.AFTER,
#     )
#     return str(doc["_id"])


# async def _upsert_category(level: str, level_id: str, field: str) -> Dict:
#     """Ensure doc in resume_categories. Increments resume_count. Returns doc."""
#     db   = get_db()
#     key  = _category_key(level, field)
#     code = _category_code(level, field)

#     return await db[COL_CATEGORIES].find_one_and_update(
#         {"category_key": key},
#         {
#             "$set": {
#                 "education_level_id": level_id,
#                 "education_level":    level,
#                 "field":              field,
#                 "category_key":       key,
#                 "category_code":      code,
#             },         
#             "$inc": {"resume_count": 1},
#             "$setOnInsert": {"created_at": datetime.now(timezone.utc)},
#         },
#         upsert=True,
#         return_document=ReturnDocument.AFTER,
#     )

         
# async def _next_resume_number(key: str) -> int:
#     """Atomically increment and return the next sequential id for this bucket."""
#     db      = get_db()
#     counter = await db[COL_COUNTERS].find_one_and_update(
#         {"_id": key},
#         {"$inc": {"seq": 1}},
#         upsert=True,
#         return_document=ReturnDocument.AFTER,
#     )
#     return counter["seq"]


# async def _resolve_category(data: Dict) -> Dict:
#     """
#     Full 3-level resolution for one parsed resume.
#     Returns the category sub-doc to embed inside the resume document.
#     """
#     education = data.get("education") or []
#     domain    = data.get("domain")    or {}

#     level     = _get_highest_level(education)
#     field     = _extract_field(education, domain)
#     key       = _category_key(level, field)

#     level_id  = await _upsert_education_level(level)
#     cat_doc   = await _upsert_category(level, level_id, field)
#     resume_no = await _next_resume_number(key)

#     return {
#         # Level 1
#         "education_level_id": level_id,
#         "education_level":    level,
#         # Level 2
#         "category_id":        str(cat_doc["_id"]),
#         "field":              field,
#         "category_key":       key,
#         "category_code":      _category_code(level, field),
#         # Level 3
#         "resume_number":      resume_no,
#     }


# # ─────────────────────────────────────────────────────────────
# # Resume document builder
# # ─────────────────────────────────────────────────────────────

# def _build_resume_doc(file_name: str, data: Dict, category: Dict) -> Dict:
#     now = datetime.now(timezone.utc)
#     return {
#         "file_name":         file_name,
#         "uploaded_at":       now,
#         "updated_at":        now,
#         "category":          category,
#         "basic_info":        data.get("basic_info",        {}),
#         "summary":           data.get("summary",           ""),
#         "education":         data.get("education",         []),
#         "experience":        data.get("experience",        []),
#         "projects":          data.get("projects",          []),
#         "skills":            data.get("skills",            {}),
#         "certifications":    data.get("certifications",    []),
#         "awards":            data.get("awards",            []),
#         "spoken_languages":  data.get("spoken_languages",  []),
#         "domain":            data.get("domain",            {}),
#         "extraction_method": data.get("extraction_method", "unknown"),
#     }


# # ─────────────────────────────────────────────────────────────
# # CRUD
# # ─────────────────────────────────────────────────────────────

# async def save_resume(file_name: str, data: Dict) -> Dict:
#     """
#     Persist a parsed resume.
#     Always succeeds — if category resolution fails for any reason
#     (e.g. Gemini 503, empty education list) the resume is stored
#     under education_level="Other", field="General".

#     Returns { resume_id, education_level, field, resume_number }.
#     """
#     import logging as _logging
#     _log = _logging.getLogger(__name__)

#     db = get_db()

#     # Category resolution is best-effort; never let it crash the upload
#     try:
#         category = await _resolve_category(data)
#     except Exception as exc:
#         _log.warning("Category resolution failed (%s); using fallback bucket.", exc)
#         fallback_level = "Other"
#         fallback_field = "General"
#         level_id       = await _upsert_education_level(fallback_level)
#         cat_doc        = await _upsert_category(fallback_level, level_id, fallback_field)
#         resume_no      = await _next_resume_number(
#             _category_key(fallback_level, fallback_field)
#         )
#         category = {
#             "education_level_id": level_id,
#             "education_level":    fallback_level,
#             "category_id":        str(cat_doc["_id"]),
#             "field":              fallback_field,
#             "category_key":       _category_key(fallback_level, fallback_field),
#             "category_code":      _category_code(fallback_level, fallback_field),
#             "resume_number":      resume_no,
#         }

#     doc    = _build_resume_doc(file_name, data, category)
#     result = await db[COL_RESUMES].insert_one(doc)
#     return {
#         "resume_id":       str(result.inserted_id),
#         "education_level": category["education_level"],
#         "field":           category["field"],
#         "resume_number":   category["resume_number"],
#     }


# async def get_resume_by_id(resume_id: str) -> Optional[Dict]:
#     db = get_db()
#     try:
#         oid = ObjectId(resume_id)
#     except Exception:
#         return None
#     doc = await db[COL_RESUMES].find_one({"_id": oid})
#     return _serialize(doc) if doc else None


# async def delete_resume(resume_id: str) -> bool:
#     try:
#         oid = ObjectId(resume_id)
#     except Exception:
#         return False
#     db     = get_db()
#     result = await db[COL_RESUMES].delete_one({"_id": oid})
#     return result.deleted_count > 0


# async def update_resume(resume_id: str, new_data: Dict) -> bool:
#     try:
#         oid = ObjectId(resume_id)
#     except Exception:
#         return False
#     db     = get_db()
#     result = await db[COL_RESUMES].update_one(
#         {"_id": oid},
#         {"$set": {**new_data, "updated_at": datetime.now(timezone.utc)}},
#     )
#     return result.modified_count > 0


# async def list_resumes(skip: int = 0, limit: int = 20) -> List[Dict]:
#     db     = get_db()
#     cursor = (
#         db[COL_RESUMES].find({})
#         .sort("uploaded_at", -1)
#         .skip(skip)
#         .limit(limit)
#     )
#     return [_serialize(doc) async for doc in cursor]


# async def count_resumes() -> int:
#     return await get_db()[COL_RESUMES].count_documents({})


# # ─────────────────────────────────────────────────────────────
# # Tree-navigation queries
# # ─────────────────────────────────────────────────────────────

# async def get_education_levels() -> List[Dict]:
#     """
#     Level 1 — all education levels with resume counts.
#     [{ "level_name": "Bachelor", "resume_count": 10 }, ...]
#     """
#     pipeline = [
#         {"$group": {
#             "_id":          "$category.education_level",
#             "resume_count": {"$sum": 1},
#         }},
#         {"$project": {"_id": 0, "level_name": "$_id", "resume_count": 1}},
#         {"$sort": {"level_name": 1}},
#     ]
#     return [doc async for doc in get_db()[COL_RESUMES].aggregate(pipeline)]


# async def get_fields_by_level(level: str) -> List[Dict]:
#     """
#     Level 2 — all fields under one education level.
#     [{ "field": "Computer Engineering", "resume_count": 5,
#        "category_key": "bachelor::computer engineering",
#        "category_code": "BCE" }, ...]
#     """
#     pipeline = [
#         {"$match": {"category.education_level": level.title()}},
#         {"$group": {
#             "_id":           "$category.field",
#             "resume_count":  {"$sum": 1},
#             "category_key":  {"$first": "$category.category_key"},
#             "category_code": {"$first": "$category.category_code"},
#         }},
#         {"$project": {
#             "_id": 0, "field": "$_id",
#             "resume_count": 1, "category_key": 1, "category_code": 1,
#         }},
#         {"$sort": {"field": 1}},
#     ]
#     return [doc async for doc in get_db()[COL_RESUMES].aggregate(pipeline)]


# async def list_resumes_by_category(level: str, field: str) -> List[Dict]:
#     """
#     Level 3 — resumes inside (level, field), ordered by resume_number.
#     Lightweight projection: only identity + basic contact shown.
#     """
#     db  = get_db()
#     key = _category_key(level, field)
#     cursor = (
#         db[COL_RESUMES]
#         .find(
#             {"category.category_key": key},
#             {
#                 "file_name":                1,
#                 "uploaded_at":              1,
#                 "basic_info.name":          1,
#                 "basic_info.emails":        1,
#                 "category.resume_number":   1,
#                 "category.education_level": 1,
#                 "category.field":           1,
#                 "domain":                   1,
#             },
#         )
#         .sort("category.resume_number", 1)
#     )
#     return [_serialize(doc) async for doc in cursor]


# async def list_resumes_by_level(level: str) -> List[Dict]:
#     """All resumes under one education level (all fields combined)."""
#     cursor = (
#         get_db()[COL_RESUMES]
#         .find({"category.education_level": level.title()})
#         .sort([("category.field", 1), ("category.resume_number", 1)])
#     )
#     return [_serialize(doc) async for doc in cursor]


# async def get_full_tree() -> List[Dict]:
#     """
#     Returns the entire category tree:
#     [
#       {
#         "level": "Bachelor",
#         "resume_count": 10,
#         "fields": [
#           {
#             "field": "Computer Engineering",
#             "resume_count": 5,
#             "category_key": "bachelor::computer engineering",
#             "category_code": "BCE"
#           }, ...
#         ]
#       }, ...
#     ]
#     """
#     pipeline = [
#         {"$group": {
#             "_id": {
#                 "level": "$category.education_level",
#                 "field": "$category.field",
#             },
#             "resume_count":  {"$sum": 1},
#             "category_key":  {"$first": "$category.category_key"},
#             "category_code": {"$first": "$category.category_code"},
#         }},
#         {"$sort": {"_id.level": 1, "_id.field": 1}},
#     ]

#     rows = [doc async for doc in get_db()[COL_RESUMES].aggregate(pipeline)]

#     tree: Dict[str, Dict] = {}
#     for row in rows:
#         lvl   = row["_id"]["level"]
#         field = row["_id"]["field"]
#         if lvl not in tree:
#             tree[lvl] = {"level": lvl, "resume_count": 0, "fields": []}
#         tree[lvl]["resume_count"] += row["resume_count"]
#         tree[lvl]["fields"].append({
#             "field":         field,
#             "resume_count":  row["resume_count"],
#             "category_key":  row["category_key"],
#             "category_code": row["category_code"],
#         })

#     return list(tree.values())


###################################################################################
# app/services/database.py
"""
SQL-backed resume storage with a 3-level tree structure:

    Education Level  (Bachelor / Master / PhD / …)
    └── Field        (Computer Engineering / Data Science / …)
        └── Resume   (resume_number 1, 2, 3 … auto-incremented per bucket)

Drop-in replacement for the previous MongoDB version.
Uses aiosqlite (SQLite) by default; swap the connection string and driver
for PostgreSQL / MySQL without touching any other file.

Dependencies:
    pip install aiosqlite
"""

import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import aiosqlite       # type: ignore

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────

DB_PATH = os.getenv("SQL_DB_PATH", "resume_db.sqlite")

# Global connection held for the lifetime of the app
_db: Optional[aiosqlite.Connection] = None


# ─────────────────────────────────────────────────────────────
# DDL – table definitions
# ─────────────────────────────────────────────────────────────

_DDL = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ── Level 1: education levels ──────────────────────────────
CREATE TABLE IF NOT EXISTS education_levels (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL UNIQUE          -- e.g. "Bachelor", "Master", "PhD"
);

-- ── Level 2: fields within a level ─────────────────────────
CREATE TABLE IF NOT EXISTS fields (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    level_id   INTEGER NOT NULL REFERENCES education_levels(id) ON DELETE CASCADE,
    name       TEXT    NOT NULL,                -- e.g. "Computer Engineering"
    UNIQUE(level_id, name)
);

-- ── Level 3: resumes inside a field bucket ─────────────────
CREATE TABLE IF NOT EXISTS resumes (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    resume_number     INTEGER NOT NULL,          -- 1-based, unique per field_id
    field_id          INTEGER NOT NULL REFERENCES fields(id) ON DELETE CASCADE,
    file_name         TEXT,
    uploaded_at       TEXT    NOT NULL,
    updated_at        TEXT    NOT NULL,
    status            TEXT    DEFAULT 'processed',

    -- Contact header (indexed columns for fast search)
    candidate_name    TEXT,
    candidate_email   TEXT,
    candidate_location TEXT,

    -- All rich structured data stored as JSON blobs
    basic_info        TEXT,   -- {"name":…, "emails":[], "phones":[], …}
    summary           TEXT,
    education         TEXT,   -- JSON array
    experience        TEXT,   -- JSON array
    total_experience  TEXT,   -- JSON: {"years":int, "months":int, "total_months":int, "display":str}
    projects          TEXT,   -- JSON array
    skills            TEXT,   -- JSON object (languages, technical, frameworks, tools, soft_skills)
    domain            TEXT,   -- JSON object
    certifications    TEXT,   -- JSON array
    awards            TEXT,   -- JSON array
    spoken_languages  TEXT,   -- JSON array
    soft_skills       TEXT,   -- JSON array
    extraction_method TEXT,

    UNIQUE(field_id, resume_number)
);

-- Fast look-ups
CREATE INDEX IF NOT EXISTS idx_resumes_field      ON resumes(field_id);
CREATE INDEX IF NOT EXISTS idx_resumes_uploaded   ON resumes(uploaded_at DESC);
CREATE INDEX IF NOT EXISTS idx_resumes_name       ON resumes(candidate_name COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_fields_level       ON fields(level_id);
"""


# ─────────────────────────────────────────────────────────────
# Connection lifecycle
# ─────────────────────────────────────────────────────────────

async def connect_db() -> None:
    global _db
    _db = await aiosqlite.connect(DB_PATH)
    _db.row_factory = aiosqlite.Row          # rows behave like dicts
    await _db.executescript(_DDL)
    await _db.commit()
    logger.info("[DB] SQLite connected → %s", DB_PATH)
    print(f"[DB] SQLite connected → {DB_PATH}")


async def close_db() -> None:
    global _db
    if _db:
        await _db.close()
        _db = None
        logger.info("[DB] SQLite connection closed.")
        print("[DB] SQLite connection closed.")


def get_db() -> aiosqlite.Connection:
    if _db is None:
        raise RuntimeError(
            "Database not initialised. Call connect_db() on startup."
        )
    return _db


# ─────────────────────────────────────────────────────────────
# Education-level extraction
# ─────────────────────────────────────────────────────────────
#
# Priority order: PhD > Master > Bachelor > Associate > Diploma
# The list is intentionally ordered highest-to-lowest so the first
# pattern that matches any education entry wins for that entry.
# Across ALL education entries we keep the globally-highest match.
#
# Regex design rules applied here:
#   1. Word boundaries (\b) prevent "ma" inside "management" from
#      being treated as an M.A. abbreviation.
#   2. Abbreviations with optional dots (b\.?s\.?) use \b on both
#      sides so they don't match mid-word.
#   3. Patterns are anchored to the start of a word where possible.
#   4. Each group is non-capturing (?:…) for efficiency.
# ─────────────────────────────────────────────────────────────

_LEVEL_PATTERNS: List[tuple] = [
    # ── PhD ─────────────────────────────────────────────────
    # Matches: PhD, Ph.D, Ph.D., DPhil, D.Phil, doctorate, doctoral
    ("PhD", re.compile(
        r"\b(?:ph\.?\s*d\.?|d\.?\s*phil\.?|doctor(?:ate|al))\b",
        re.IGNORECASE,
    )),

    # ── Master ───────────────────────────────────────────────
    # Matches: Master, Masters, Master's, MS, M.S, MSc, M.Sc,
    #          MEng, M.Eng, MTech, M.Tech, MPhil, MBA, MA, M.A
    # NOTE: "ma" alone is NOT matched — requires a word boundary on
    #       both sides, so "management" is safe.
    ("Master", re.compile(
        r"\b(?:"
        r"masters?(?:'s)?"             # Master / Masters / Master's
        r"|m\.?\s*s\.?\s*c?\.?"        # MS / M.S / MSc / M.Sc
        r"|m\.?\s*eng\.?"              # MEng / M.Eng
        r"|m\.?\s*tech\.?"             # MTech / M.Tech
        r"|m\.?\s*phil\.?"             # MPhil / M.Phil
        r"|m\.?\s*b\.?\s*a\.?"         # MBA / M.B.A
        r"|m\.?\s*a\.?"                # MA / M.A  (word-boundary protected)
        r")\b",
        re.IGNORECASE,
    )),

    # ── Bachelor ─────────────────────────────────────────────
    # Matches: Bachelor, Bachelors, Bachelor's, BS, B.S, BSc, B.Sc,
    #          BE, B.E, BTech, B.Tech, BEng, B.Eng, BA, B.A,
    #          undergraduate, honours / honors
    ("Bachelor", re.compile(
        r"\b(?:"
        r"bachelors?(?:'s)?"           # Bachelor / Bachelors / Bachelor's
        r"|b\.?\s*s\.?\s*c?\.?"        # BS / B.S / BSc / B.Sc
        r"|b\.?\s*e\.?"                # BE / B.E
        r"|b\.?\s*tech\.?"             # BTech / B.Tech
        r"|b\.?\s*eng\.?"              # BEng / B.Eng
        r"|b\.?\s*a\.?"                # BA / B.A
        r"|undergraduate"
        r"|honours?"                   # honours / honor
        r")\b",
        re.IGNORECASE,
    )),

    # ── Associate ────────────────────────────────────────────
    # Matches: Associate, Associates, AA, A.A, AS, A.S
    ("Associate", re.compile(
        r"\b(?:"
        r"associates?(?:'s)?"          # Associate / Associates
        r"|a\.?\s*a\.?"                # AA / A.A
        r"|a\.?\s*s\.?"                # AS / A.S
        r")\b",
        re.IGNORECASE,
    )),

    # ── Diploma ──────────────────────────────────────────────
    # Matches: Diploma, Certificate Program, Certificate Course
    ("Diploma", re.compile(
        r"\b(?:diploma|certificate\s+(?:program|course|of))\b",
        re.IGNORECASE,
    )),
]

# Rank map: lower number = higher priority
_LEVEL_RANK: Dict[str, int] = {
    name: idx for idx, (name, _) in enumerate(_LEVEL_PATTERNS)
}


def _extract_education_level(data: Dict) -> str:
    """
    Scan ALL education entries and return the HIGHEST degree level found.

    Strategy (in order of preference):
      1. Check each education entry's degree, field, institution, and
         description fields — combining them into one searchable string.
      2. If no education list exists or none matched, fall back to the
         raw summary text (some resumes mention degrees in the summary).
      3. Default to 'Other' if nothing matches.

    "Highest" means closest to index 0 in _LEVEL_PATTERNS
    (PhD=0, Master=1, Bachelor=2, Associate=3, Diploma=4).
    """
    edu_list = data.get("education") or []
    if not isinstance(edu_list, list):
        edu_list = []

    best_rank: int = 999
    best_level: str = "Other"

    for edu in edu_list:
        if not isinstance(edu, dict):
            continue

        # Combine every text field available in this education entry so
        # we catch degrees written as "B.Sc Computer Science" in the
        # institution field, etc.
        searchable = " ".join(
            str(edu.get(key, "") or "")
            for key in ("degree", "field", "major", "institution", "school", "description")
        ).strip()

        if not searchable:
            continue

        # Walk patterns highest-to-lowest; stop at first match for this
        # entry (an entry can only count as one level).
        for level_name, pattern in _LEVEL_PATTERNS:
            if pattern.search(searchable):
                rank = _LEVEL_RANK[level_name]
                if rank < best_rank:
                    best_rank = rank
                    best_level = level_name
                break  # only the highest level per entry counts

    # ── Fallback: scan summary text ──────────────────────────────────────
    # Some resumes don't have a structured education list but mention their
    # degree in the professional summary (e.g. "PhD candidate in ML …").
    if best_level == "Other":
        summary = str(data.get("summary", "") or "")
        if summary:
            for level_name, pattern in _LEVEL_PATTERNS:
                if pattern.search(summary):
                    best_level = level_name
                    break  # summary fallback: take the first (highest) match

    return best_level


def _extract_field(data: Dict, level: str) -> str:
    """
    Extract the academic field / major from the education entry that
    corresponds to the already-identified level.

    Priority:
      1. Explicit 'field' or 'major' key in the matching education entry
      2. Degree string with the degree prefix stripped away
      3. First education entry's field/degree if no level match found
      4. 'General' as the final fallback
    """
    edu_list = data.get("education") or []
    if not isinstance(edu_list, list):
        return "General"

    # Find the pattern for the identified level
    level_pattern = next(
        (pat for name, pat in _LEVEL_PATTERNS if name == level), None
    )

    first_entry_field: Optional[str] = None  # best-effort fallback

    for edu in edu_list:
        if not isinstance(edu, dict):
            continue

        degree = str(edu.get("degree", "") or "").strip()

        # ── Capture the first entry's field as a fallback ────────────────
        if first_entry_field is None:
            candidate = (
                str(edu.get("field",  "") or "").strip() or
                str(edu.get("major",  "") or "").strip() or
                _strip_degree_prefix(degree)
            )
            if candidate:
                first_entry_field = _title_case_field(candidate)

        # ── Only process entries that match our identified level ──────────
        if level_pattern and degree and not level_pattern.search(degree):
            continue

        # Prefer explicit field / major keys
        for key in ("field", "major"):
            val = str(edu.get(key, "") or "").strip()
            if val:
                return _title_case_field(val)

        # Fall back: strip the degree prefix from the degree string
        # e.g. "Bachelor of Science in Computer Engineering" → "Computer Engineering"
        stripped = _strip_degree_prefix(degree)
        if stripped:
            return _title_case_field(stripped)

    # Use first entry's field if the level-matched loop found nothing
    return first_entry_field or "General"


def _strip_degree_prefix(degree: str) -> str:
    """
    Remove common degree prefixes from a degree string, returning only
    the subject/field part.

    Examples:
      "Bachelor of Science in Computer Engineering" → "Computer Engineering"
      "M.Sc Data Science"                          → "Data Science"
      "PhD"                                         → ""
    """
    if not degree:
        return ""

    # Remove the degree-type token(s) at the start
    stripped = re.sub(
        r"^(?:"
        r"ph\.?\s*d\.?|d\.?\s*phil\.?|doctor(?:ate|al)|"
        r"masters?(?:'s)?|m\.?\s*s\.?\s*c?\.?|m\.?\s*eng\.?|"
        r"m\.?\s*tech\.?|m\.?\s*phil\.?|m\.?\s*b\.?\s*a\.?|m\.?\s*a\.?|"
        r"bachelors?(?:'s)?|b\.?\s*s\.?\s*c?\.?|b\.?\s*e\.?|"
        r"b\.?\s*tech\.?|b\.?\s*eng\.?|b\.?\s*a\.?|"
        r"associates?(?:'s)?|diploma"
        r")[\s,\-–—.]*",
        "",
        degree,
        flags=re.IGNORECASE,
    ).strip()

    # Remove leading connective words like "of", "in", "science", etc.
    stripped = re.sub(
        r"^(?:of|in|science|arts|engineering|technology|applied)\s+",
        "",
        stripped,
        flags=re.IGNORECASE,
    ).strip()

    return stripped


def _title_case_field(s: str) -> str:
    """Normalise a field name to Title Case, treating minor words correctly."""
    if not s:
        return "General"
    minor = {"of", "in", "and", "the", "for", "a", "an", "&"}
    words = s.strip().split()
    result = [
        word if (i > 0 and word.lower() in minor) else word.capitalize()
        for i, word in enumerate(words)
    ]
    return " ".join(result) if result else "General"


# ─────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _dumps(val: Any) -> Optional[str]:
    """Safely JSON-serialise; returns None for missing/None values."""
    if val is None:
        return None
    return json.dumps(val, ensure_ascii=False, default=str)


def _loads(val: Optional[str]) -> Any:
    """Safely JSON-deserialise; returns None on error."""
    if val is None:
        return None
    try:
        return json.loads(val)
    except Exception:
        return val


def _row_to_dict(row) -> Dict:
    """Convert an aiosqlite.Row to a plain dict."""
    return dict(row) if row else {}


def _deserialize_resume(row) -> Dict:
    """
    Convert a raw DB row into the full resume dict expected by the API,
    JSON-decoding every blob column.
    """
    d = _row_to_dict(row)
    if not d:
        return {}

    json_cols = (
        "basic_info", "education", "experience", "total_experience", "projects",
        "skills", "domain", "certifications", "awards",
        "spoken_languages", "soft_skills",
    )
    for col in json_cols:
        d[col] = _loads(d.get(col))

    return d


# ─────────────────────────────────────────────────────────────
# Tree helpers – get-or-create
# ─────────────────────────────────────────────────────────────

async def _get_or_create_level(db: aiosqlite.Connection, level_name: str) -> int:
    async with db.execute(
        "SELECT id FROM education_levels WHERE name = ?", (level_name,)
    ) as cur:
        row = await cur.fetchone()
    if row:
        return row["id"]
    async with db.execute(
        "INSERT INTO education_levels (name) VALUES (?)", (level_name,)
    ) as cur:
        return cur.lastrowid


async def _get_or_create_field(
    db: aiosqlite.Connection, level_id: int, field_name: str
) -> int:
    async with db.execute(
        "SELECT id FROM fields WHERE level_id = ? AND name = ?",
        (level_id, field_name),
    ) as cur:
        row = await cur.fetchone()
    if row:
        return row["id"]
    async with db.execute(
        "INSERT INTO fields (level_id, name) VALUES (?, ?)",
        (level_id, field_name),
    ) as cur:
        return cur.lastrowid


async def _next_resume_number(db: aiosqlite.Connection, field_id: int) -> int:
    """Return next sequential 1-based number within this field bucket."""
    async with db.execute(
        "SELECT COALESCE(MAX(resume_number), 0) + 1 FROM resumes WHERE field_id = ?",
        (field_id,),
    ) as cur:
        row = await cur.fetchone()
    return row[0] if row else 1


# ─────────────────────────────────────────────────────────────
# CRUD – save
# ─────────────────────────────────────────────────────────────

async def save_resume(file_name: str, data: Dict) -> Dict:
    """
    Insert a resume and return:
        {
            "resume_id":       int,
            "education_level": str,   e.g. "Bachelor"
            "field":           str,   e.g. "Computer Engineering"
            "resume_number":   int,   e.g. 3
        }
    """
    db = get_db()
    now = _now_iso()

    # ── Determine tree position ──────────────────────────────────────────
    education_level = _extract_education_level(data)
    field           = _extract_field(data, education_level)

    logger.info("[DB] Extracted level=%s field=%s for %s", education_level, field, file_name)

    # ── Resolve / create tree nodes ──────────────────────────────────────
    level_id = await _get_or_create_level(db, education_level)
    field_id = await _get_or_create_field(db, level_id, field)
    res_num  = await _next_resume_number(db, field_id)

    # ── Flatten contact info for indexed columns ──────────────────────────
    basic = data.get("basic_info") or {}
    candidate_name     = str(basic.get("name", "")     or "").strip() or None
    candidate_email    = (basic.get("emails") or [""])[0] or None
    candidate_location = str(basic.get("location", "") or "").strip() or None

    skills = data.get("skills") or {}

    await db.execute(
        """
        INSERT INTO resumes (
            resume_number, field_id, file_name, uploaded_at, updated_at, status,
            candidate_name, candidate_email, candidate_location,
            basic_info, summary, education, experience, total_experience, projects,
            skills, domain, certifications, awards, spoken_languages,
            soft_skills, extraction_method
        ) VALUES (
            ?, ?, ?, ?, ?, 'processed',
            ?, ?, ?,
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?
        )
        """,
        (
            res_num, field_id, file_name, now, now,
            candidate_name, candidate_email, candidate_location,
            _dumps(basic),
            data.get("summary", ""),
            _dumps(data.get("education", [])),
            _dumps(data.get("experience", [])),
            _dumps(data.get("total_experience")),
            _dumps(data.get("projects", [])),
            _dumps(skills),
            _dumps(data.get("domain")),
            _dumps(data.get("certifications", [])),
            _dumps(data.get("awards", [])),
            _dumps(data.get("spoken_languages", [])),
            _dumps(skills.get("soft_skills", [])),
            data.get("extraction_method", "regex_rule"),
        ),
    )
    await db.commit()

    # Fetch the auto-assigned id
    async with db.execute("SELECT last_insert_rowid()") as cur:
        row = await cur.fetchone()
    resume_id = row[0]

    logger.info(
        "[DB] Saved resume id=%d → %s > %s > #%d",
        resume_id, education_level, field, res_num,
    )

    return {
        "resume_id":       resume_id,
        "education_level": education_level,
        "field":           field,
        "resume_number":   res_num,
    }


# ─────────────────────────────────────────────────────────────
# CRUD – read one
# ─────────────────────────────────────────────────────────────

async def get_resume_by_id(resume_id: str) -> Optional[Dict]:
    """
    Fetch a single resume by its integer primary key.
    Returns a fully-deserialised dict including tree metadata.
    """
    try:
        rid = int(resume_id)
    except (ValueError, TypeError):
        return None

    db = get_db()
    async with db.execute(
        """
        SELECT
            r.*,
            f.name  AS field_name,
            el.name AS level_name
        FROM resumes r
        JOIN fields           f  ON f.id  = r.field_id
        JOIN education_levels el ON el.id = f.level_id
        WHERE r.id = ?
        """,
        (rid,),
    ) as cur:
        row = await cur.fetchone()

    if not row:
        return None

    result = _deserialize_resume(row)
    result["education_level"] = result.pop("level_name", None)
    result["field"]           = result.pop("field_name", None)
    return result


# ─────────────────────────────────────────────────────────────
# CRUD – list / count
# ─────────────────────────────────────────────────────────────

async def list_resumes(skip: int = 0, limit: int = 20) -> List[Dict]:
    """Flat paginated list with summary fields only."""
    db = get_db()
    async with db.execute(
        """
        SELECT
            r.id, r.resume_number, r.file_name, r.uploaded_at,
            r.candidate_name, r.extraction_method, r.status,
            f.name  AS field,
            el.name AS education_level,
            r.domain
        FROM resumes r
        JOIN fields           f  ON f.id  = r.field_id
        JOIN education_levels el ON el.id = f.level_id
        ORDER BY r.uploaded_at DESC
        LIMIT ? OFFSET ?
        """,
        (limit, skip),
    ) as cur:
        rows = await cur.fetchall()

    results = []
    for row in rows:
        d = _row_to_dict(row)
        d["domain"] = _loads(d.get("domain"))
        results.append(d)
    return results


async def count_resumes() -> int:
    db = get_db()
    async with db.execute("SELECT COUNT(*) FROM resumes") as cur:
        row = await cur.fetchone()
    return row[0] if row else 0


# ─────────────────────────────────────────────────────────────
# CRUD – update
# ─────────────────────────────────────────────────────────────

async def update_resume(resume_id: str, new_data: Dict) -> bool:
    try:
        rid = int(resume_id)
    except (ValueError, TypeError):
        return False

    db = get_db()
    result = await db.execute(
        """
        UPDATE resumes
        SET
            updated_at        = ?,
            basic_info        = COALESCE(?, basic_info),
            summary           = COALESCE(?, summary),
            education         = COALESCE(?, education),
            experience        = COALESCE(?, experience),
            total_experience  = COALESCE(?, total_experience),
            projects          = COALESCE(?, projects),
            skills            = COALESCE(?, skills),
            domain            = COALESCE(?, domain),
            certifications    = COALESCE(?, certifications),
            awards            = COALESCE(?, awards),
            spoken_languages  = COALESCE(?, spoken_languages),
            extraction_method = COALESCE(?, extraction_method)
        WHERE id = ?
        """,
        (
            _now_iso(),
            _dumps(new_data.get("basic_info")),
            new_data.get("summary"),
            _dumps(new_data.get("education")),
            _dumps(new_data.get("experience")),
            _dumps(new_data.get("total_experience")),
            _dumps(new_data.get("projects")),
            _dumps(new_data.get("skills")),
            _dumps(new_data.get("domain")),
            _dumps(new_data.get("certifications")),
            _dumps(new_data.get("awards")),
            _dumps(new_data.get("spoken_languages")),
            new_data.get("extraction_method"),
            rid,
        ),
    )
    await db.commit()
    return result.rowcount > 0


# ─────────────────────────────────────────────────────────────
# CRUD – delete
# ─────────────────────────────────────────────────────────────

async def delete_resume(resume_id: str) -> bool:
    try:
        rid = int(resume_id)
    except (ValueError, TypeError):
        return False

    db = get_db()
    result = await db.execute("DELETE FROM resumes WHERE id = ?", (rid,))
    await db.commit()
    return result.rowcount > 0


# ─────────────────────────────────────────────────────────────
# Tree navigation
# ─────────────────────────────────────────────────────────────

async def get_full_tree() -> List[Dict]:
    """
    Return the complete tree:
        [
          {
            "level": "Bachelor",
            "total": 12,
            "fields": [
              {"field": "Computer Engineering", "count": 5, "level_id": 1, "field_id": 2},
              ...
            ]
          },
          ...
        ]
    """
    db = get_db()
    async with db.execute(
        """
        SELECT
            el.id   AS level_id,
            el.name AS level,
            f.id    AS field_id,
            f.name  AS field,
            COUNT(r.id) AS resume_count
        FROM education_levels el
        JOIN fields   f ON f.level_id = el.id
        LEFT JOIN resumes r ON r.field_id = f.id
        GROUP BY el.id, f.id
        ORDER BY el.name, f.name
        """
    ) as cur:
        rows = await cur.fetchall()

    tree: Dict[str, Dict] = {}
    for row in rows:
        lvl = row["level"]
        if lvl not in tree:
            tree[lvl] = {"level": lvl, "level_id": row["level_id"],
                         "total": 0, "fields": []}
        tree[lvl]["fields"].append({
            "field":    row["field"],
            "field_id": row["field_id"],
            "count":    row["resume_count"],
        })
        tree[lvl]["total"] += row["resume_count"]

    return list(tree.values())


async def get_education_levels() -> List[Dict]:
    """
    Return all education levels with resume counts.
        [{"level": "Bachelor", "level_id": 1, "total": 12}, …]
    """
    db = get_db()
    async with db.execute(
        """
        SELECT
            el.id   AS level_id,
            el.name AS level,
            COUNT(r.id) AS total
        FROM education_levels el
        LEFT JOIN fields  f ON f.level_id = el.id
        LEFT JOIN resumes r ON r.field_id = f.id
        GROUP BY el.id
        ORDER BY el.name
        """
    ) as cur:
        rows = await cur.fetchall()
    return [_row_to_dict(r) for r in rows]


async def get_fields_by_level(level_name: str) -> List[Dict]:
    """
    Return all fields under a level with resume counts.
        [{"field": "Computer Engineering", "field_id": 2, "count": 5}, …]
    """
    db = get_db()
    async with db.execute(
        """
        SELECT
            f.id    AS field_id,
            f.name  AS field,
            COUNT(r.id) AS count
        FROM fields f
        JOIN education_levels el ON el.id = f.level_id
        LEFT JOIN resumes r ON r.field_id = f.id
        WHERE el.name = ? COLLATE NOCASE
        GROUP BY f.id
        ORDER BY f.name
        """,
        (level_name,),
    ) as cur:
        rows = await cur.fetchall()
    return [_row_to_dict(r) for r in rows]


async def list_resumes_by_category(level_name: str, field_name: str) -> List[Dict]:
    """
    All resumes inside one exact level + field bucket.
    Returns summary cards (no heavy JSON blobs).
    """
    db = get_db()
    async with db.execute(
        """
        SELECT
            r.id, r.resume_number, r.file_name, r.uploaded_at,
            r.candidate_name, r.candidate_email, r.candidate_location,
            r.extraction_method, r.status
        FROM resumes r
        JOIN fields           f  ON f.id  = r.field_id
        JOIN education_levels el ON el.id = f.level_id
        WHERE el.name = ? COLLATE NOCASE
          AND f.name  = ? COLLATE NOCASE
        ORDER BY r.resume_number
        """,
        (level_name, field_name),
    ) as cur:
        rows = await cur.fetchall()
    return [_row_to_dict(r) for r in rows]


async def list_resumes_by_level(level_name: str) -> List[Dict]:
    """
    All resumes under one education level (across all fields).
    Returns summary cards grouped by field.
    """
    db = get_db()
    async with db.execute(
        """
        SELECT
            r.id, r.resume_number, r.file_name, r.uploaded_at,
            r.candidate_name, r.candidate_email, r.candidate_location,
            r.extraction_method, r.status,
            f.name AS field
        FROM resumes r
        JOIN fields           f  ON f.id  = r.field_id
        JOIN education_levels el ON el.id = f.level_id
        WHERE el.name = ? COLLATE NOCASE
        ORDER BY f.name, r.resume_number
        """,
        (level_name,),
    ) as cur:
        rows = await cur.fetchall()
    return [_row_to_dict(r) for r in rows]


# ─────────────────────────────────────────────────────────────
# Search
# ─────────────────────────────────────────────────────────────

async def search_resumes(
    level:   Optional[str] = None,
    field:   Optional[str] = None,
    number:  Optional[int] = None,
    name:    Optional[str] = None,
    keyword: Optional[str] = None,
    skip:    int = 0,
    limit:   int = 50,
) -> Dict:
    """
    Multi-field search across all resume text content.

    Keyword search covers: candidate name, file name, summary, skills
    (JSON blob), basic_info (JSON blob), experience (JSON blob), and
    candidate email.  Because skills/experience are stored as JSON
    strings, a LIKE '%python%' correctly matches any resume that mentions
    Python anywhere inside those blobs.
    """
    db = get_db()

    conditions: List[str] = []
    params: List[Any] = []

    # ── Education Level ───────────────────────────────────────────────
    if level and level.strip().lower() not in ("all", ""):
        conditions.append("el.name = ? COLLATE NOCASE")
        params.append(level.strip())

    # ── Field ─────────────────────────────────────────────────────────
    if field and field.strip():
        conditions.append("f.name = ? COLLATE NOCASE")
        params.append(field.strip())

    # ── Exact resume number ───────────────────────────────────────────
    if number is not None:
        conditions.append("r.resume_number = ?")
        params.append(number)

    # ── Specific name search ──────────────────────────────────────────
    if name and name.strip():
        conditions.append("r.candidate_name LIKE ? COLLATE NOCASE")
        params.append(f"%{name.strip()}%")

    # ── Keyword search ────────────────────────────────────────────────
    # Searches across: name, file name, summary, skills blob, basic_info
    # blob, experience blob, and email.  The JSON blobs are searched as
    # raw text (LIKE on the serialised JSON string) which is fast enough
    # for SQLite at typical resume-database scale and requires no FTS5.
    if keyword and keyword.strip():
        k = keyword.strip()
        like = f"%{k}%"
        conditions.append(
            """(
                r.candidate_name  LIKE ? COLLATE NOCASE
                OR r.file_name    LIKE ? COLLATE NOCASE
                OR r.summary      LIKE ? COLLATE NOCASE
                OR r.skills       LIKE ?
                OR r.basic_info   LIKE ?
                OR r.experience   LIKE ?
                OR r.education    LIKE ?
                OR r.certifications LIKE ?
                OR COALESCE(r.candidate_email, '') LIKE ? COLLATE NOCASE
            )"""
        )
        params.extend([like] * 9)

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    # ── Count ──────────────────────────────────────────────────────────
    count_sql = f"""
        SELECT COUNT(*)
        FROM resumes r
        JOIN fields           f  ON f.id  = r.field_id
        JOIN education_levels el ON el.id = f.level_id
        {where_clause}
    """
    async with db.execute(count_sql, params) as cur:
        row = await cur.fetchone()
    total = row[0] if row else 0

    # ── Fetch ──────────────────────────────────────────────────────────
    data_sql = f"""
        SELECT
            r.id,
            r.resume_number,
            r.file_name,
            r.uploaded_at,
            r.candidate_name,
            r.candidate_email,
            r.candidate_location,
            r.extraction_method,
            r.status,
            r.summary,
            r.skills,
            r.domain,
            r.basic_info,
            f.name  AS field,
            el.name AS education_level
        FROM resumes r
        JOIN fields           f  ON f.id  = r.field_id
        JOIN education_levels el ON el.id = f.level_id
        {where_clause}
        ORDER BY r.uploaded_at DESC, r.id DESC
        LIMIT ? OFFSET ?
    """
    async with db.execute(data_sql, params + [limit, skip]) as cur:
        rows = await cur.fetchall()

    items = []
    for row in rows:
        d = _row_to_dict(row)
        d["domain"]    = _loads(d.get("domain"))
        d["skills"]    = _loads(d.get("skills"))
        d["basic_info"] = _loads(d.get("basic_info"))
        items.append(d)

    return {
        "items": items,
        "total": total,
        "skip":  skip,
        "limit": limit,
    }