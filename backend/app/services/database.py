# app/services/database.py
"""
SQL-backed resume storage with a 3-level tree structure:

    Education Level  (Bachelor / Master / PhD / …)
    └── Field        (Computer Engineering / Data Science / …)
        └── Resume   (resume_number 1, 2, 3 … auto-incremented per bucket)

Uses aiosqlite (SQLite) by default; swap the connection string and driver for PostgreSQL / MySQL without touching any other file.

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
