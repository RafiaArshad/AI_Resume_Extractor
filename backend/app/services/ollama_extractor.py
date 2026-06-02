# app/services/ollama_extractor.py
"""
Gemini-based structured resume extraction 
"""

import json
import logging
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, List, Optional


# ─────────────────────────────────────────────────────────────
# ENV LOADER
# ─────────────────────────────────────────────────────────────

def _load_dotenv() -> None:
    for candidate in (
        os.path.join(os.path.dirname(__file__), "..", ".env"),
        ".env",
    ):
        if not os.path.exists(candidate):
            continue
        try:
            with open(candidate, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
        except OSError:
            pass
        break


_load_dotenv()
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# GEMINI CONFIG
# ─────────────────────────────────────────────────────────────

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL   = "gemini-2.5-flash"
GEMINI_URL     = f"https://generativelanguage.googleapis.com/v1/models/{GEMINI_MODEL}:generateContent"
TIMEOUT        = 120
MAX_CHARS      = 20000
MAX_RETRIES    = 3
RETRY_DELAY    = 20


# ─────────────────────────────────────────────────────────────
# PRE-PROCESSING
# ─────────────────────────────────────────────────────────────

# Tokens that must be split when written as a slash-pair
_SLASH_SPLIT_PAIRS: List[tuple] = [
    (r"\bC\s*/\s*C\+\+",       "C, C++"),      # C/C++   → C, C++
    (r"\bC\+\+\s*/\s*C\b",     "C++, C"),      # C++/C   → C++, C
    (r"\bHTML\s*/\s*CSS\b",     "HTML, CSS"),   # HTML/CSS → HTML, CSS
    (r"\bReact\s*/\s*Next\b",   "React, Next.js"),
    (r"\bReact\s*/\s*Next\.js\b", "React, Next.js"),
    (r"\bNode\s*/\s*Express\b",  "Node.js, Express.js"),
    (r"\bPython\s*/\s*Django\b", "Python, Django"),
    (r"\bJava\s*/\s*Spring\b",   "Java, Spring"),
]


def _preprocess_resume_text(text: str) -> str:
    """
    Normalise slash-fused tokens BEFORE sending to the LLM.
    This prevents the model from ignoring or mangling 'C/C++'.
    Also normalises common formatting issues.
    """
    for pattern, replacement in _SLASH_SPLIT_PAIRS:
        text = re.sub(pattern, replacement, text)
    # Normalise multiple spaces
    text = re.sub(r"[ \t]{2,}", " ", text)
    # Normalise bullet points
    text = re.sub(r"^[•\-\*◦▪●]\s*", "- ", text, flags=re.MULTILINE)
    return text


def _smart_truncate(text: str, max_chars: int = MAX_CHARS) -> str:
    """Truncate text at sentence boundary to preserve context."""
    if len(text) <= max_chars:
        return text
    # Try to find last sentence boundary before max_chars
    truncated = text[:max_chars]
    # Look for sentence endings: ., !, ? followed by space or newline
    last_sentence = re.search(r"[.!?]\s+", truncated[::-1])
    if last_sentence:
        cut_point = max_chars - last_sentence.start()
        return text[:cut_point].strip()
    # Fallback: truncate at last newline
    last_newline = truncated.rfind("\n")
    if last_newline > max_chars * 0.8:
        return text[:last_newline].strip()
    return truncated.strip()


# ─────────────────────────────────────────────────────────────
# SYSTEM PROMPT  (all improvements encoded)
# ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a precision resume parsing engine. Extract information from raw resume text into a strict JSON object.

ABSOLUTE RULE: Extract ONLY what is EXPLICITLY present in the text.
Never infer, guess, hallucinate, or use world-knowledge to fill gaps.

═══════════════════════════════════════════
OUTPUT FORMAT
═══════════════════════════════════════════
- Output ONE valid JSON object. Nothing else.
- No markdown, no code fences (```), no comments, no trailing commas.
- Missing single value → null | Missing string → "" | Missing list → []
- Never omit a required key.
- The FIRST character MUST be { and the LAST MUST be }.

═══════════════════════════════════════════
SCHEMA
═══════════════════════════════════════════
{
  "basic_info": {
    "name":     null,   // Full name — first 3 lines only; 2–5 words, letters/spaces/hyphens
    "emails":   [],     // RFC-valid email addresses only
    "phones":   [],     // Phone numbers, preserve original formatting
    "location": null,   // *** SEE LOCATION RULES BELOW ***
    "links":    []      // Valid URLs: LinkedIn, GitHub, portfolio only
  },
  "summary": "",        // Verbatim; "" if absent
  "education": [{
    "institution": "",
    "degree":      "",
    "field":       "",
    "duration":    "",
    "gpa":         null,
    "coursework":  []   // Relevant courses listed under this degree ONLY
  }],
  "experience": [{
    "role":             "",
    "company":          "",
    "duration":         "",
    "location":         "",   // "" if not stated; "Remote" is valid
    "is_current":       false,
    "responsibilities": []
  }],
  "projects": [{
    "name":        "",
    "description": [],
    "tech_stack":  [],
    "links":       []
  }],
  "skills": {
    "languages": {
      "high_level": [],   // *** SEE LANGUAGE RULES BELOW ***
      "low_level":  []
    },
    "technical":  [],
    "frameworks": [],
    "tools":      []
  },
  "soft_skills":     [],
  "certifications":  [],   // *** SEE CERTIFICATION RULES BELOW ***
  "awards":          [],
  "spoken_languages":[],   // *** SEE SPOKEN LANGUAGE RULES BELOW ***
  "domain": {
    "name":       null,
    "confidence": 0,
    "breakdown":  {}
  },
  "extraction_method": "llm_hybrid"
}

═══════════════════════════════════════════
LOCATION RULES  [CRITICAL]
═══════════════════════════════════════════
RULE: Set location to the EXACT city/region/country string that is PHYSICALLY PRINTED
      in the contact section of the resume. Nothing else.

✓ ALLOWED  — "Lahore, Pakistan"  /  "New York, NY"  /  "Remote"  /  "Islamabad"
✗ FORBIDDEN — Guessing a city from a university name (e.g. NUST → do NOT write "Islamabad")
✗ FORBIDDEN — Guessing a city from a company name
✗ FORBIDDEN — Constructing a location from partial clues
✗ FORBIDDEN — Any value you are not 100% certain is printed verbatim in the header/contact block
✗ FORBIDDEN — Full street addresses (e.g. "123 Main St, Suite 4")

If no explicit location string is present in the contact section → "location": null

═══════════════════════════════════════════
CERTIFICATION RULES  [CRITICAL]
═══════════════════════════════════════════
Include an entry ONLY when ALL three conditions are met:
  (a) The item uses certification language: "Certified", "Certificate", "Certification", "License", "Credential", "Accredited", "Badge"
  (b) A named external issuer is identifiable (e.g. AWS, Google, Coursera, Microsoft, Cisco, Oracle, IBM, Meta)
  (c) It is listed in a Certifications / Licenses / Credentials section OR clearly presented as an external credential elsewhere

EXPLICITLY EXCLUDE:
  ✗ Soft skills (Communication, Leadership, Problem Solving, Teamwork, Time Management) — put those in soft_skills
  ✗ University courses or coursework — put those in education[].coursework
  ✗ Hackathon participation / workshop attendance without a certificate
  ✗ Self-described proficiencies ("proficient in Python", "skilled in Java")
  ✗ Tools or technologies listed without certification context ("Docker", "Kubernetes" alone)
  ✗ Activities, societies, or extracurriculars
  ✗ Any item where you cannot identify both certification language AND an issuer
  ✗ Internal company training without external credential

CERTIFICATION OBJECT SCHEMA:
{
  "name":          "",    // Exact title as written
  "issuer":        null,  // Issuing organisation; null if genuinely absent
  "date":          null,  // Exact as written: "2023", "Jan 2024"; null if absent
  "credential_id": null,
  "url":           null
}

═══════════════════════════════════════════
SKILLS → LANGUAGE RULES
═══════════════════════════════════════════
languages is a DICT with two sub-lists:

  high_level  — human-readable, garbage-collected, or scripted languages:
    Python, JavaScript, TypeScript, Java, C#, Ruby, PHP, Swift, Kotlin,
    Go, Scala, R, MATLAB, Dart, Lua, Perl, Haskell, Elixir, Erlang,
    Groovy, Visual Basic, COBOL, Fortran, Bash/Shell, Julia, Objective-C

  low_level   — close-to-hardware, systems, or compiled languages with
                manual memory management:
    C, C++, Rust, Assembly, Ada, Verilog, VHDL, Forth, Zig

CRITICAL — C / C++ handling:
  • The resume text may write "C/C++", "C / C++", "C, C++" or list them separately.
  • ALWAYS place "C" in low_level AND "C++" in low_level as two separate entries.
  • NEVER omit either one, and NEVER write "C/C++" as a single string in output.
  • SQL is NOT a programming language — place it in tools[].

NORMALISATION (apply before placing):
  ReactJS / React JS → "React"       (→ frameworks)
  NodeJS / Node JS   → "Node.js"     (→ frameworks)
  sklearn            → "scikit-learn"(→ frameworks)
  postgres / pg      → "PostgreSQL"  (→ tools)
  TF / TensorFlow variants → "TensorFlow" (→ frameworks)

No skill appears in more than one category across the entire skills object.

═══════════════════════════════════════════
SPOKEN LANGUAGE RULES  [CRITICAL]
═══════════════════════════════════════════
Extract ONLY human spoken languages (NOT programming languages).

✓ ALLOWED: "English", "Urdu", "Hindi", "Spanish", "French", "German", "Chinese", "Arabic", "Bengali", "Russian", "Portuguese", "Japanese", "Punjabi", "Sindhi", "Pashto", "Balochi"
✗ FORBIDDEN: "Python", "Java", "C++", "SQL", "HTML", "JavaScript"

Format: Include proficiency level if present in text:
  "English (Fluent)", "Urdu (Native)", "Spanish (Intermediate)"
  If no proficiency level is stated, output just the language name: "English"

If the text writes "Languages: English, Urdu" without proficiency levels,
output: ["English", "Urdu"]

If the text writes "Languages: English (Fluent), Urdu (Native)",
output: ["English (Fluent)", "Urdu (Native)"]

═══════════════════════════════════════════
COURSEWORK → SKILLS PROHIBITION
═══════════════════════════════════════════
RULE: Courses listed under a university or college degree are ACADEMIC SUBJECTS,
      not technical skills. They belong ONLY in education[].coursework.

✗ NEVER copy course names into skills.technical, skills.frameworks, or anywhere in skills.
✗ NEVER interpret a course title as a technology skill.

Examples of what NOT to do:
  Course "Database Systems" → do NOT add "Database Systems" to skills.technical
  Course "Machine Learning" → do NOT add "Machine Learning" to skills.technical
  Course "Data Structures"  → do NOT add "Data Structures" to skills.technical

The only way coursework should appear in output is inside education[N].coursework[].
5
═══════════════════════════════════════════
GENERAL SKILL PLACEMENT RULES
═══════════════════════════════════════════
technical:  Concepts/methodologies — ML, NLP, RAG, REST API, CI/CD, OOP, Agile, Microservices, System Design, Data Structures, Algorithms, Cloud Computing, DevOps
frameworks: TensorFlow, PyTorch, React, FastAPI, LangChain, spaCy, NLTK, HuggingFace/Transformers, OpenAI API, LlamaIndex, Chainlit, NumPy, Pandas, SciPy, Matplotlib, Seaborn, scikit-learn, Django, Flask, Spring Boot, Next.js, Vue.js, Angular, Express.js, Bootstrap, Tailwind CSS

tools:      AWS, Docker, Git, PostgreSQL, MySQL, MongoDB, Redis, Postman, ChromaDB, Pinecone, Jupyter, VS Code, Linux, Firebase, Heroku, Vercel, Nginx, Apache, Jenkins, GitHub Actions, Kubernetes, Terraform, Ansible, Grafana, Prometheus, Postman, Insomnia, Figma, Jira, Confluence, Slack, Trello, WordPress

soft_skills: Leadership, Communication, Teamwork, Critical Thinking, Problem Solving, Time Management, Adaptability, Creativity, Attention to Detail, Collaboration, Negotiation, Presentation Skills, Conflict Resolution, Decision Making, Strategic Thinking, Empathy, Mentoring, Coaching

Extract skills from: Skills section, experience bullets, project tech_stacks.
NLP libs (spaCy, NLTK, Transformers, HuggingFace) → frameworks, NOT tools.
Data science libs (NumPy, Pandas, SciPy, Matplotlib, Seaborn) → frameworks, NOT tools.

═══════════════════════════════════════════
OTHER RULES
═══════════════════════════════════════════
DATES: Preserve exactly as written. "Present"/"Current"/"Now" → is_current: true.
AWARDS: Plain strings from dedicated sections AND inline education mentions.
DOMAIN: snake_case — ai_ml | data_science | backend_engineering | frontend_engineering
        | full_stack | devops_cloud | cybersecurity | mobile_development | research | other
        breakdown values must sum to exactly 100.
"""


# ─────────────────────────────────────────────────────────────
# OLLAMA COMPATIBILITY SHIMS
# ─────────────────────────────────────────────────────────────

def is_ollama_available() -> bool:
    return bool(GEMINI_API_KEY)


def get_available_models() -> List[str]:
    return [GEMINI_MODEL] if GEMINI_API_KEY else []


def get_best_model() -> Optional[str]:
    return GEMINI_MODEL if GEMINI_API_KEY else None


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def _prepare_text(text: str) -> str:
    """Truncate + pre-process before sending to LLM."""
    text = _preprocess_resume_text(text)
    return _smart_truncate(text, MAX_CHARS)


def _post_json(url: str, payload: Dict, timeout: int):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return res.getcode(), res.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8")


def _parse_json_robust(raw: str) -> Optional[Dict]:
    if not raw:
        return None

    raw = re.sub(r"```json|```", "", raw).strip()

    try:
        return json.loads(raw)
    except Exception:
        pass

    start, end = raw.find("{"), raw.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(raw[start : end + 1])
        except Exception:
            pass

    return None


def _ensure_list_of_strings(val) -> List[str]:
    """Guarantee List[str]. Handles list-of-strings, list-of-dicts, None."""
    if not isinstance(val, list):
        return []
    out = []
    for item in val:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
        elif isinstance(item, dict):
            name = str(item.get("name", "") or "").strip()
            if name:
                out.append(name)
    return out


# ─────────────────────────────────────────────────────────────
# LANGUAGE SANITIZER
# ─────────────────────────────────────────────────────────────

# Canonical mapping of low-level languages (lowercase → display name)
_LOW_LEVEL_LANGS = {
    "c":        "C",
    "c++":      "C++",
    "rust":     "Rust",
    "assembly": "Assembly",
    "asm":      "Assembly",
    "ada":      "Ada",
    "verilog":  "Verilog",
    "vhdl":     "VHDL",
    "forth":    "Forth",
    "zig":      "Zig",
}

_HIGH_LEVEL_LANGS = {
    "python", "javascript", "typescript", "java", "c#", "ruby", "php",
    "swift", "kotlin", "go", "scala", "r", "matlab", "dart", "lua",
    "perl", "haskell", "elixir", "erlang", "groovy", "visual basic",
    "cobol", "fortran", "bash", "shell", "sh", "zsh", "ksh",
    "powershell", "julia", "objective-c", "f#", "vb.net",
    "html", "css", "sass", "scss", "sql", "plsql", "tsql",
    "crystal", "nim", "smalltalk", "clojure", "lisp", "scheme",
    "awk", "tcl", "sas", "stata",
}


def _sanitize_languages(val) -> Dict[str, List[str]]:
    """
    Accepts:
      (a) {"high_level": [...], "low_level": [...]}   ← new schema
      (b) flat list ["Python", "C++", ...]             ← old schema / fallback
      (c) anything else → empty buckets

    Also splits any surviving "C/C++" tokens → "C" + "C++" in low_level.
    Returns: {"high_level": [...], "low_level": [...]}
    """
    high: List[str] = []
    low:  List[str] = []

    if isinstance(val, dict):
        raw_high = _ensure_list_of_strings(val.get("high_level", []))
        raw_low  = _ensure_list_of_strings(val.get("low_level",  []))
    elif isinstance(val, list):
        # LLM returned flat list — re-classify by canonical lookup
        raw_flat = _ensure_list_of_strings(val)
        raw_low  = [t for t in raw_flat if t.lower() in _LOW_LEVEL_LANGS]
        raw_high = [t for t in raw_flat if t.lower() not in _LOW_LEVEL_LANGS]
    else:
        return {"high_level": [], "low_level": []}

    # ── Expand any "C/C++" that survived pre-processing ──────────────────
    def _expand_slash_c(tokens: List[str]) -> List[str]:
        expanded = []
        for tok in tokens:
            if re.match(r"^[Cc]\s*/\s*[Cc]\+\+$", tok):
                expanded.append("C")
                expanded.append("C++")
            elif re.match(r"^[Cc]\+\+\s*/\s*[Cc]$", tok):
                expanded.append("C++")
                expanded.append("C")
            else:
                expanded.append(tok)
        return expanded

    raw_high = _expand_slash_c(raw_high)
    raw_low  = _expand_slash_c(raw_low)

    # ── Re-bucket anything that ended up in the wrong list ────────────────
    for tok in raw_high[:]:
        if tok.lower() in _LOW_LEVEL_LANGS:
            raw_high.remove(tok)
            canonical = _LOW_LEVEL_LANGS[tok.lower()]
            if canonical not in raw_low:
                raw_low.append(canonical)

    for tok in raw_low[:]:
        canonical = _LOW_LEVEL_LANGS.get(tok.lower())
        if canonical and canonical not in low:
            low.append(canonical)

    # ── Build final high list (deduplicated, normalised) ─────────────────
    seen = set()
    for tok in raw_high:
        key = tok.lower()
        if key not in seen and key not in _LOW_LEVEL_LANGS:
            seen.add(key)
            high.append(tok)

    return {"high_level": high, "low_level": low}


# ─────────────────────────────────────────────────────────────
# CERTIFICATION SANITIZER
# ─────────────────────────────────────────────────────────────

# Keywords that must appear in a real certification name
_CERT_KEYWORDS = re.compile(
    r"\b(certif(ied|icate|ication)|licen[sc]e|accreditation|badge|credential|"
    r"nanodegree|specialization|professional|associate|practitioner|expert|"
    r"foundation|fundamentals|essentials|advanced|developer|architect)\b",
    re.IGNORECASE,
)

# Phrases that flag a false-positive certification
_CERT_BLACKLIST = re.compile(
    r"\b(communication|leadership|teamwork|problem.?solving|adaptability|"
    r"time.?management|critical.?thinking|collaboration|workshop|"
    r"hackathon|bootcamp|seminar|webinar|training|course|class|"
    r"volunteering|membership|society|club|honor|dean|soft.?skill|"
    r"interpersonal|negotiation|presentation|conflict.?resolution|"
    r"decision.?making|strategic.?thinking|empathy|mentoring|coaching)\b",
    re.IGNORECASE,
)

# Known legitimate certification issuers
_KNOWN_ISSUERS = {
    "aws", "amazon", "google", "microsoft", "cisco", "oracle", "ibm", "meta",
    "facebook", "coursera", "udemy", "linkedin", "edx", "pluralsight",
    "datacamp", "codecademy", "deeplearning.ai", "fast.ai", "kaggle",
    "mongodb", "red hat", "hashicorp", "terraform", "kubernetes", "cncf",
    "comptia", "isc2", "ec-council", "offensive security", "isc²",
    "salesforce", "adobe", "autodesk", "pmi", "pmi-pmp", "pmp",
    "scrum", "safe", "scaled agile", "itil", "togaf",
}


def _sanitize_certifications(certs) -> List[Dict]:
    """
    Hard-filter: keep only entries that look like genuine external certifications.
    An entry is kept when:
      - name contains a cert keyword  OR  issuer is a known credential org
      - name does NOT match the blacklist
    """
    if not isinstance(certs, list):
        return []

    cleaned = []
    for cert in certs:
        if not isinstance(cert, dict):
            continue

        name   = str(cert.get("name",   "") or "").strip()
        issuer = str(cert.get("issuer", "") or "").strip().lower()

        if not name:
            continue

        name_lower = name.lower()
        has_cert_kw = bool(_CERT_KEYWORDS.search(name))
        has_issuer  = bool(issuer)
        is_known_issuer = any(ki in issuer for ki in _KNOWN_ISSUERS)
        is_blacklisted = bool(_CERT_BLACKLIST.search(name))

        if is_blacklisted:
            logger.debug("Cert dropped (blacklist): %s", name)
            continue

        # Must have cert keyword OR known issuer
        if not (has_cert_kw or is_known_issuer):
            logger.debug("Cert dropped (no keyword+issuer): %s", name)
            continue

        # If no issuer and no strong cert keyword, drop it
        if not issuer and not has_cert_kw:
            logger.debug("Cert dropped (no issuer and weak keyword): %s", name)
            continue

        cleaned.append({
            "name":          name,
            "issuer":        cert.get("issuer") or None,
            "date":          cert.get("date")          or None,
            "credential_id": cert.get("credential_id") or None,
            "url":           cert.get("url")           or None,
        })

    return cleaned


# ─────────────────────────────────────────────────────────────
# SPOKEN LANGUAGE SANITIZER
# ─────────────────────────────────────────────────────────────

# Valid spoken languages (common)
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

# Programming languages to EXCLUDE from spoken languages
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

# Proficiency levels
_PROFICIENCY_PATTERN = re.compile(
    r"\s*\((native|fluent|proficient|intermediate|beginner|basic|"
    r"elementary|pre-intermediate|upper-intermediate|advanced|"
    r"conversational|working|professional|limited|mother.?tongue)\)",
    re.IGNORECASE,
)


def _sanitize_spoken_languages(spoken) -> List[str]:
    """
    Clean and validate spoken languages.
    Remove programming languages, invalid entries, and normalize format.
    """
    if not isinstance(spoken, list):
        return []

    cleaned = []
    seen = set()

    for item in spoken:
        if not isinstance(item, str):
            continue
        item = item.strip()
        if not item:
            continue

        # Extract language name (remove proficiency in parentheses for matching)
        lang_match = re.match(r"^([^(]+)", item)
        if not lang_match:
            continue
        lang_name = lang_match.group(1).strip().lower()

        # Skip programming languages
        if lang_name in _PROG_LANGS:
            logger.debug("Spoken lang dropped (prog lang): %s", item)
            continue

        # Skip if not a valid spoken language
        if lang_name not in _VALID_SPOKEN_LANGS:
            # Check if it contains a valid language as substring
            found_valid = False
            for valid in _VALID_SPOKEN_LANGS:
                if valid in lang_name or lang_name in valid:
                    found_valid = True
                    break
            if not found_valid:
                logger.debug("Spoken lang dropped (unknown): %s", item)
                continue

        # Deduplicate
        key = lang_name
        if key in seen:
            continue
        seen.add(key)

        # Normalize: keep original casing for display but standardise common ones
        # Extract proficiency if present
        prof_match = _PROFICIENCY_PATTERN.search(item)
        if prof_match:
            prof = prof_match.group(1).title()
            # Reconstruct with proper casing
            display_name = lang_name.title()
            cleaned.append(f"{display_name} ({prof})")
        else:
            cleaned.append(lang_name.title())

    return cleaned


# ─────────────────────────────────────────────────────────────
# LOCATION SANITIZER
# ─────────────────────────────────────────────────────────────

# University / company sub-strings that sometimes bleed into location
_INSTITUTION_NOISE = re.compile(
    r"\b(university|college|institute|school|of|the|and|for|at|"
    r"corp|inc\.?|ltd\.?|pvt|limited|technologies|solutions|"
    r"systems|software|services|company|group|consulting|"
    r"international|national|global|academy|polytechnic)\b",
    re.IGNORECASE,
)

# Patterns that look fabricated (full mailing addresses)
_ADDRESS_NOISE = re.compile(
    r"\b(street|st\.?|avenue|ave\.?|road|rd\.?|block|sector|phase|"
    r"house|floor|flat|apt|apartment|suite|po box|p\.o\.box|"
    r"building|tower|plaza|complex|village|colony|township)\b",
    re.IGNORECASE,
)

# Valid country names for validation
_VALID_COUNTRIES = {
    "pakistan", "india", "bangladesh", "nepal", "sri lanka",
    "united states", "usa", "united kingdom", "uk", "uae", "canada",
    "australia", "germany", "france", "china", "japan", "singapore",
    "new zealand", "south africa", "nigeria", "kenya", "egypt",
    "saudi arabia", "qatar", "kuwait", "bahrain", "oman", "jordan",
    "lebanon", "syria", "iraq", "iran", "turkey", "afghanistan",
    "malaysia", "indonesia", "thailand", "philippines", "vietnam",
    "south korea", "north korea", "taiwan", "hong kong", "macau",
    "brazil", "argentina", "chile", "peru", "colombia", "venezuela",
    "mexico", "cuba", "jamaica", "trinidad and tobago", "barbados",
    "italy", "spain", "portugal", "netherlands", "belgium", "switzerland",
    "austria", "sweden", "norway", "denmark", "finland", "ireland",
    "poland", "czech republic", "slovakia", "hungary", "romania",
    "bulgaria", "croatia", "serbia", "bosnia", "montenegro", "albania",
    "greece", "cyprus", "malta", "iceland", "luxembourg", "monaco",
    "russia", "ukraine", "belarus", "moldova", "georgia", "armenia",
    "azerbaijan", "kazakhstan", "uzbekistan", "turkmenistan", "tajikistan",
    "kyrgyzstan", "mongolia", "remote", "hybrid",
}

# Valid city patterns (common cities)
_COMMON_CITIES = {
    "lahore", "karachi", "islamabad", "rawalpindi", "faisalabad",
    "multan", "peshawar", "quetta", "sialkot", "gujranwala",
    "hyderabad", "sukkur", "bahawalpur", "sargodha", "sheikhupura",
    "jhelum", "gujrat", "kasur", "rahim yar khan", "sahiwal",
    "mumbai", "delhi", "bangalore", "chennai", "kolkata", "pune",
    "ahmedabad", "jaipur", "lucknow", "kanpur", "nagpur", "indore",
    "thane", "bhopal", "visakhapatnam", "vadodara", "firozabad",
    "ludhiana", "rajkot", "agra", "siliguri", "durgapur", "chandigarh",
    "dehradun", "shimla", "srinagar", "jammu", "amritsar", "jalandhar",
    "patiala", "bathinda", "new york", "los angeles", "chicago",
    "houston", "phoenix", "philadelphia", "san antonio", "san diego",
    "dallas", "san jose", "austin", "jacksonville", "fort worth",
    "columbus", "charlotte", "san francisco", "indianapolis", "seattle",
    "denver", "washington", "boston", "el paso", "detroit", "nashville",
    "portland", "oklahoma city", "las vegas", "louisville", "baltimore",
    "milwaukee", "albuquerque", "tucson", "fresno", "sacramento",
    "mesa", "kansas city", "atlanta", "long beach", "colorado springs",
    "raleigh", "omaha", "miami", "oakland", "minneapolis", "tulsa",
    "cleveland", "wichita", "arlington", "london", "manchester",
    "birmingham", "leeds", "glasgow", "sheffield", "bradford",
    "liverpool", "edinburgh", "cardiff", "belfast", "dublin",
    "toronto", "vancouver", "montreal", "calgary", "ottawa",
    "edmonton", "quebec", "winnipeg", "hamilton", "kitchener",
    "sydney", "melbourne", "brisbane", "perth", "adelaide",
    "gold coast", "newcastle", "canberra", "wollongong",
    "dubai", "abu dhabi", "sharjah", "ajman", "ras al khaimah",
    "fujairah", "umm al quwain", "doha", "riyadh", "jeddah",
    "mecca", "medina", "damascus", "beirut", "amman", "baghdad",
    "tehran", "istanbul", "ankara", "izmir", "kabul", "kuala lumpur",
    "singapore", "jakarta", "bangkok", "manila", "hanoi", "ho chi minh",
    "seoul", "busan", "tokyo", "osaka", "kyoto", "yokohama",
    "nagoya", "sapporo", "fukuoka", "kobe", "kawasaki", "hiroshima",
    "beijing", "shanghai", "guangzhou", "shenzhen", "chengdu",
    "hangzhou", "wuhan", "xian", "nanjing", "tianjin", "chongqing",
    "hong kong", "taipei", "kaohsiung", "são paulo", "rio de janeiro",
    "brasília", "salvador", "fortaleza", "belo horizonte", "manaus",
    "curitiba", "recife", "porto alegre", "buenos aires", "cordoba",
    "rosario", "mendoza", "santiago", "valparaíso", "concepción",
    "lima", "arequipa", "trujillo", "bogotá", "medellín", "cali",
    "cartagena", "caracas", "maracaibo", "valencia", "maracay",
    "barquisimeto", "ciudad de méxico", "guadalajara", "monterrey",
    "puebla", "tijuana", "león", "ciudad juárez", "cancún",
    "havana", "santiago de cuba", "camagüey", "holguín", "kingston",
    "port of spain", "bridgetown",
    "berlin", "hamburg", "munich", "cologne", "frankfurt", "stuttgart",
    "düsseldorf", "dortmund", "essen", "leipzig", "bremen", "dresden",
    "hanover", "nuremberg", "duisburg", "bochum", "wuppertal",
    "paris", "marseille", "lyon", "toulouse", "nice", "nantes",
    "strasbourg", "montpellier", "bordeaux", "lille", "rennes",
    "reims", "le havre", "saint-étienne", "toulon", "grenoble",
    "rome", "milan", "naples", "turin", "palermo", "genoa",
    "bologna", "florence", "bari", "catania", "venice", "verona",
    "madrid", "barcelona", "valencia", "seville", "zaragoza",
    "málaga", "murcia", "palma", "las palmas", "bilbao", "alicante",
    "cordoba", "valladolid", "vigo", "gijón", "l'hospitalet",
    "amsterdam", "rotterdam", "the hague", "utrecht", "eindhoven",
    "tilburg", "groningen", "almere", "breda", "nijmegen",
    "brussels", "antwerp", "ghent", "charleroi", "liège", "bruges",
    "namur", "leuven", "mons",
    "zurich", "geneva", "basel", "bern", "lausanne", "lucerne",
    "st. gallen", "lugano", "winterthur",
    "vienna", "graz", "linz", "salzburg", "innsbruck", "klagenfurt",
    "villach", "wels", "sankt pölten",
    "stockholm", "gothenburg", "malmö", "uppsala", "västerås",
    "örebro", "linköping", "helsingborg", "jönköping", "norrköping",
    "oslo", "bergen", "trondheim", "stavanger", "drammen",
    "fredrikstad", "kristiansand", "tromsø", "sandnes",
    "copenhagen", "aarhus", "odense", "aalborg", "frederiksberg",
    "esbjerg", "gentofte", "gladsaxe", "randers",
    "helsinki", "espoo", "tampere", "vantaa", "oulu", "turku",
    "jyväskylä", "lahti", "kuopio", "pori", "joensuu",
    "warsaw", "kraków", "łódź", "wrocław", "poznań", "gdańsk",
    "szczecin", "bydgoszcz", "lublin", "katowice", "białystok",
    "prague", "brno", "ostrava", "plzeň", "liberec", "olomouc",
    "budapest", "debrecen", "szeged", "miskolc", "pécs", "győr",
    "nyíregyháza", "kecskemét", "székesfehérvár",
    "bucharest", "cluj-napoca", "timișoara", "iași", "constanța",
    "craiova", "brașov", "galați", "ploiești", "oradea",
    "sofia", "plovdiv", "varna", "burgas", "ruse", "stara zagora",
    "zagreb", "split", "rijeka", "osijek", "zadar", "pula",
    "belgrade", "novi sad", "niš", "kragujevac", "subotica",
    "ljubljana", "maribor", "celje", "kranj", "velenje",
    "sarajevo", "banja luka", "tuzla", "zenica", "mostar",
    "podgorica", "nikšić", "pljevlja", "bijelo polje", "bar",
    "tirana", "durres", "vlore", "elbasan", "shkoder", "fier",
    "athens", "thessaloniki", "patras", "heraklion", "larissa",
    "nicosia", "limassol", "larnaca", "famagusta", "paphos",
    "valletta", "birkirkara", "mosta", "sliema", "qormi",
    "reykjavik", "kopavogur", "hafnarfjordur", "akureyri", "gardabaer",
    "luxembourg", "esch-sur-alzette", "differdange", "dudelange", "ettelbruck",
    "monaco", "monte carlo", "la condamine", "fontvieille",
    "moscow", "saint petersburg", "novosibirsk", "yekaterinburg",
    "kazan", "nizhny novgorod", "chelyabinsk", "samara", "omsk",
    "rostov-on-don", "ufa", "krasnoyarsk", "voronezh", "perm",
    "kyiv", "kharkiv", "odesa", "dnipro", "donetsk", "zaporizhzhia",
    "lviv", "mykolaiv", "mariupol", "luhansk", "vinnytsia",
    "minsk", "gomel", "mogilev", "vitebsk", "hrodna", "brest",
    "chisinau", "tiraspol", "bălți", "bender", "rîbnița",
    "tbilisi", "kutaisi", "batumi", "rustavi", "zugdidi",
    "yerevan", "gyumri", "vanadzor", "vagharshapat", "hrazdan",
    "baku", "ganja", "sumqayit", "mingachevir", "shirvan",
    "astana", "almaty", "shymkent", "aktobe", "taraz", "pavlodar",
    "tashkent", "namangan", "samarkand", "andijan", "nukus", "fergana",
    "ashgabat", "turkmenabat", "daşoguz", "mary", "balkanabat",
    "dushanbe", "khujand", "kulob", "bokhtar", "istaravshan",
    "bishkek", "osh", "jalal-abad", "karakol", "naryn", "talas",
    "ulan bator", "erdenet", "darkhan", "choibalsan", "mörön",
    "nairobi", "mombasa", "kisumu", "nakuru", "eldoret", "meru",
    "lagos", "kano", "ibadan", "kaduna", "port harcourt", "benin city",
    "maiduguri", "zaria", "aba", "ilorin", "jos", "owerri",
    "addis ababa", "dire dawa", "mekelle", "gondar", "hawassa", "bahir dar",
    "mogadishu", "hargeisa", "bosaso", "garowe", "kismayo", "berbera",
    "kampala", "gulu", "lira", "mbarara", "jinja", "entebbee",
    "kigali", "butare", "gitarama", "ruhengeri", "gisenyi", "byumba",
    "bujumbura", "gitega", "ngozi", "rumonge", "cibitoke", "makamba",
    "dar es salaam", "mwanza", "arusha", "dodoma", "mbeya", "morogoro",
    "lilongwe", "blantyre", "mzuzu", "zomba", "karonga", "kasungu",
    "lusaka", "kitwe", "ndola", "kabwe", "chingola", "mufulira",
    "harare", "bulawayo", "chitungwiza", "mutare", "gweru", "kwekwe",
    "maputo", "matola", "nampula", "beira", "chimoio", "nacala",
    "windhoek", "walvis bay", "swakopmund", "ondangwa", "rundu", "oshakati",
    "gaborone", "francistown", "molepolole", "maun", "serowe", "kanye",
    "maseru", "mafeteng", "leribe", "mohale's hoek", "quthing", "butha-buthe",
    "mbabane", "manzini", "big bend", "malkerns", "nhlangano", "hlatikulu",
    "cairo", "alexandria", "giza", "shubra el kheima", "port said", "suez",
    "casablanca", "fez", "tangier", "marrakesh", "salé", "meknes",
    "tunis", "sfax", "sousse", "kairouan", "bizerte", "gabès",
    "algiers", "oran", "constantine", "annaba", "blida", "batna",
    "tripoli", "benghazi", "misrata", "zawiya", "bayda", " Sabha",
    "khartoum", "omdurman", "bahri", "port sudan", "kassala", "el obeid",
    "juba", "wau", "malakal", "yei", "aweil", "renk",
    "asmara", "keren", "massawa", "assab", "mendefera", "barentu",
    "djibouti", "ali sabieh", "tadjoura", "obock", "dikhil", "art",
    "pretoria", "cape town", "durban", "johannesburg", "soweto", "port elizabeth",
    "gqeberha", "bloemfontein", "nelspruit", "polokwane", "kimberley",
    "luanda", "huambo", "lobito", "benguela", "kuito", "lubango",
    "kinshasa", "lubumbashi", "mbuji-mayi", "kananga", "kisangani", "bukavu",
    "brazzaville", "pointe-noire", "dolisie", "nkayi", "impfondo", "owando",
    "libreville", "port-gentil", "franceville", "oyem", "moanda", "lambarene",
    "malabo", "bata", "ebebiyin", "mongomo", "anisoc", "evinayong",
    "yaoundé", "douala", "garoua", "bamenda", "maroua", "bafoussam",
    "bangui", "bimbo", "berberati", "carnot", "bambari", "bossangoa",
    "n'djamena", "moundou", "sarh", "abeche", "doba", "koumra",
    "niamey", "zinder", "maradi", "tahoua", "agadez", "dosso",
    "ouagadougou", "bobo-dioulasso", "koudougou", "banfora", "ouahigouya", "pô",
    "bamako", "sikasso", "kalabancoro", "koutiala", "ségou", "kayes",
    "conakry", "nzérékoré", "kankan", "kindia", "labé", "boké",
    "freetown", "bo", "kenema", "makeni", "koidu", "port loko",
    "monrovia", "gbarnga", "kakata", "bensonville", "harper", "voinjama",
    "yamoussoukro", "abidjan", "bouaké", "daloa", "san-pédro", "korhogo",
    "accra", "kumasi", "tamale", "sekondi-takoradi", "ashaiman", "tema",
    "lomé", "sokodé", "kara", "atakpame", "palimé", "dapaong",
    "porto-novo", "cotonou", "parakou", "djougou", "bohicon", "abomey",
    "abuja", "lagos", "kano", "ibadan", "kaduna", "port harcourt",
    "yaoundé", "douala", "libreville", "malabo", "bangui", "n'djamena",
}


def _sanitize_location(loc) -> Optional[str]:
    """
    Return the location only if it looks like a genuine city/region string
    and does NOT contain institution or street-address noise.
    Returns None on suspicion of hallucination.
    """
    if not isinstance(loc, str) or not loc.strip():
        return None

    loc = loc.strip()

    # Reject suspiciously long location strings (likely fabricated)
    if len(loc) > 60:
        logger.debug("Location dropped (too long): %s", loc)
        return None

    # Reject if contains institution noise
    if _INSTITUTION_NOISE.search(loc):
        logger.debug("Location dropped (institution noise): %s", loc)
        return None

    # Reject if contains address noise
    if _ADDRESS_NOISE.search(loc):
        logger.debug("Location dropped (address noise): %s", loc)
        return None

    # Validate against known cities/countries
    loc_lower = loc.lower()
    has_valid_city = any(city in loc_lower for city in _COMMON_CITIES)
    has_valid_country = any(country in loc_lower for country in _VALID_COUNTRIES)

    # If it has a known city or country, it's likely valid
    if has_valid_city or has_valid_country:
        return loc

    # Check pattern: "City, Country" or "City, ST" (state abbreviation)
    if re.match(r"^[A-Za-z][A-Za-z\s\-\.]{1,30},\s*[A-Za-z][A-Za-z\s]{1,30}$", loc):
        return loc

    # Check if it's just "Remote" or "Hybrid"
    if loc_lower in {"remote", "hybrid"}:
        return loc.title()

    logger.debug("Location dropped (no validation match): %s", loc)
    return None


# ─────────────────────────────────────────────────────────────
# MASTER SANITIZER
# ─────────────────────────────────────────────────────────────

def _sanitize(data: Dict) -> Dict:
    """
    Enforce safe, typed schema on raw Gemini output.
    Applies all fixes post-extraction as a safety net.
    """

    # ── Basic info / location ─────────────────────────────────────────────
    basic = data.get("basic_info")
    if isinstance(basic, dict):
        basic["location"] = _sanitize_location(basic.get("location"))
        basic["emails"]   = _ensure_list_of_strings(basic.get("emails"))
        basic["phones"]   = _ensure_list_of_strings(basic.get("phones"))
        basic["links"]    = _ensure_list_of_strings(basic.get("links"))
        data["basic_info"] = basic

    # ── Skills ────────────────────────────────────────────────────────────
    skills = data.get("skills")
    if not isinstance(skills, dict):
        skills = {}

    data["skills"] = {
        "languages": _sanitize_languages(skills.get("languages")),
        "technical":  _ensure_list_of_strings(skills.get("technical")),
        "frameworks": _ensure_list_of_strings(skills.get("frameworks")),
        "tools":      _ensure_list_of_strings(skills.get("tools")),
    }

    # ── Soft skills ───────────────────────────────────────────────────────
    data["soft_skills"] = _ensure_list_of_strings(data.get("soft_skills"))

    # ── Awards ────────────────────────────────────────────────────────────
    data["awards"] = _ensure_list_of_strings(data.get("awards"))

    # ── Certifications ──────────────────────────────────────────────────────
    data["certifications"] = _sanitize_certifications(data.get("certifications"))

    # ── Spoken languages ──────────────────────────────────────────────────
    data["spoken_languages"] = _sanitize_spoken_languages(data.get("spoken_languages"))

    # ── Experience ────────────────────────────────────────────────────────
    for exp in data.get("experience", []) or []:
        if isinstance(exp, dict):
            exp["responsibilities"] = _ensure_list_of_strings(
                exp.get("responsibilities")
            )
            # Sanitise per-experience location too
            exp["location"] = _sanitize_location(exp.get("location")) or ""

    # ── Projects ──────────────────────────────────────────────────────────
    for proj in data.get("projects", []) or []:
        if not isinstance(proj, dict):
            continue
        proj["description"] = _ensure_list_of_strings(proj.get("description"))
        proj["tech_stack"]  = _ensure_list_of_strings(proj.get("tech_stack"))
        proj["links"]       = _ensure_list_of_strings(proj.get("links"))

    # ── Education: coursework must NOT leak into skills ─────────
    all_coursework: set = set()
    for edu in data.get("education", []) or []:
        if isinstance(edu, dict):
            cw = _ensure_list_of_strings(edu.get("coursework"))
            edu["coursework"] = cw
            all_coursework.update(c.lower() for c in cw)

    if all_coursework:
        for cat in ("technical", "frameworks", "tools"):
            data["skills"][cat] = [
                s for s in data["skills"][cat]
                if s.lower() not in all_coursework
            ]
        # Also purge from flat language lists
        for bucket in ("high_level", "low_level"):
            data["skills"]["languages"][bucket] = [
                s for s in data["skills"]["languages"][bucket]
                if s.lower() not in all_coursework
            ]

    # ── Domain validation ──────────────────────────────────────────────────
    domain = data.get("domain")
    if isinstance(domain, dict):
        conf = domain.get("confidence", 0)
        if isinstance(conf, (int, float)) and conf < 0.7:
            # Low confidence domain — clear it
            data["domain"] = {"name": None, "confidence": 0, "breakdown": {}}

    return data


# ─────────────────────────────────────────────────────────────
# MAIN FUNCTION
# ─────────────────────────────────────────────────────────────

def extract_with_ollama(text: str) -> Dict:
    """
    Gemini-powered structured extraction.
    Returns {} on ANY failure — never raises.
    Implements retry logic with exponential backoff.
    """
    if not GEMINI_API_KEY:
        logger.debug("GEMINI_API_KEY not set — skipping LLM extraction")
        return {}

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": SYSTEM_PROMPT},
                    {
                        "text": (
                            "Parse this resume and return ONLY the JSON object. "
                            "No preamble, no explanation.\n\n"
                            + _prepare_text(text)
                        )
                    },
                ]
            }
        ],
        "generationConfig": {
            "temperature":     0.0,
            "topP":            0.95,
            "topK":            1,
            "maxOutputTokens": 8192,
        },
    }

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            url = f"{GEMINI_URL}?{urllib.parse.urlencode({'key': GEMINI_API_KEY})}"
            status, body = _post_json(url, payload, TIMEOUT)

            if status == 429:  # Rate limited
                wait_time = RETRY_DELAY * (2 ** attempt)
                logger.warning("Gemini rate limited, waiting %ds...", wait_time)
                time.sleep(wait_time)
                continue

            if status != 200:
                logger.warning("Gemini API error %s: %s", status, body[:200])
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (2 ** attempt))
                    continue
                return {}

            raw_text = (
                json.loads(body)
                .get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )

            parsed = _parse_json_robust(raw_text)
            if isinstance(parsed, dict):
                return _sanitize(parsed)

            logger.warning("Gemini returned non-dict JSON: %s", type(parsed))
            return {}

        except Exception as e:
            last_error = e
            logger.exception("Gemini extraction failed (attempt %d)", attempt + 1)
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (2 ** attempt))

    logger.error("All %d Gemini extraction attempts failed. Last error: %s", MAX_RETRIES, last_error)
    return {}
