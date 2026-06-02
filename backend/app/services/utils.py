import re
from typing import Any, Dict, List, Optional

# ============================================================
# SECTION HEADERS
# ============================================================

SECTION_HEADERS: Dict[str, List[str]] = {
    "summary": [
        "summary", "profile", "objective", "about me", "about",
        "professional summary", "career objective", "overview",
        "career profile", "personal statement", "executive summary",
        "professional profile", "personal profile", "introduction",
        "professional overview", "bio",
    ],
    "education": [
        "education", "academic background", "academic",
        "qualifications", "educational background",
        "academic qualifications", "educational qualifications",
        "academic history", "education and training",
        "education & training", "scholastic details",
    ],
    "experience": [
        "experience", "work experience", "professional experience",
        "employment history", "internship", "internships",
        "work history", "career history", "employment",
        "professional background", "relevant experience",
        "industry experience", "practical experience",
        "experience and employment", "experience & employment",
        "job experience", "professional work experience",
        "positions held", "career experience",
    ],
    "skills": [
        "skills", "technical skills", "core competencies",
        "technologies", "tech stack", "tools",
        "libraries and frameworks", "libraries & frameworks",
        "key skills", "skills & technologies",
        "skills and technologies", "technical expertise",
        "technical proficiencies", "areas of expertise",
        "competencies", "programming skills",
        "software skills", "it skills", "hard skills",
        "skills and tools", "skills & tools",
    ],
    "projects": [
        "projects", "project experience", "personal projects",
        "academic projects", "key projects", "notable projects",
        "selected projects", "portfolio", "side projects",
        "open source", "independent projects", "project work",
        "major projects", "relevant projects",
    ],

    "certifications": [
        "certification", "certifications", "certificates",
        "certificate", "licensed",
        "licenses", "licenses and certifications",
        "licenses & certifications",
        "professional certifications",
        "credentials", "accreditations",
        "training and certifications",
        "training & certifications",
        "certifications and training",
        "certifications & training",
        "certifications and achievements",
        "certifications & achievements",
        "achievements and certifications",
        "professional development & certifications",
        "professional development and certifications",
    ],

    "courses": [
        "courses", "online courses", "relevant courses",
        "relevant coursework", "related coursework",
        "courses taken", "completed courses",
        "academic courses", "moocs", "e-learning",
        "udemy courses", "coursera courses",
        "continuing education",
        "professional development",
        "training",
    ],

    "awards": [
        "awards", "achievements", "honors",
        "awards & honors", "awards and honors",
        "recognitions", "honors & awards",
        "scholarships", "accomplishments",
        "distinctions", "prizes",
    ],
    "languages": [
        "languages", "language proficiency",
        "spoken languages", "language skills",
        "linguistic skills", "languages known",
    ],
}

# ============================================================
# REGEX PATTERNS
# ============================================================

EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    re.I,
)

_PHONE_FULL_RE = re.compile(
    r"(?<![.\w])"
    r"("
      r"(?:\(?\+\d{1,3}\)?[\s.\-]{0,2})"
      r"(?:\(?\d{2,4}\)?[\s.\-]{0,2})?"
      r"\d{3,5}[\s.\-]?\d{4,7}"
    r"|"
      r"(?:00\d{2,3}[\s.\-]{0,2})"
      r"(?:\(?\d{2,4}\)?[\s.\-]{0,2})?"
      r"\d{3,5}[\s.\-]?\d{4,7}"
    r"|"
      r"(?:\(0\d{1,4}\)[\s.\-]{0,2})"
      r"\d{3,5}[\s.\-]?\d{4,7}"
    r"|"
      r"(?:0\d{2,4}[\s.\-]{0,2})"
      r"\d{3,5}[\s.\-]?\d{4,7}"
    r")"
    r"(?![.\d])",
)

URL_REGEX = re.compile(
    r"(https?://[^\s<>\"',;)]+|(?:www|linkedin|github|gitlab|bitbucket)\.[^\s<>\"',;)]+)",
    re.I,
)

DATE_RANGE_REGEX = re.compile(
    r"(?P<start>"
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)?"
    r"\s*'?\d{2,4})"
    r"\s*(?:\u2013|-|\u2014|to|till|until)\s*"
    r"(?P<end>"
    r"(?:Present|Current|Now|Ongoing|"
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
    r"\s*'?\d{2,4}|"
    r"\d{4}))",
    re.I,
)

DATE_SINGLE_REGEX = re.compile(
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
    r"\s+'?\d{2,4}",
    re.I,
)

DATE_YEAR_ONLY_REGEX = re.compile(r"(?<!\d)((?:19|20)\d{2})(?!\d)")

LOCATION_REGEX = re.compile(
    r"^[A-Za-z][A-Za-z\s\-\.]{1,30},\s*[A-Za-z][A-Za-z\s]{1,30}$"
)

GPA_REGEX = re.compile(
    r"(?:gpa|cgpa|grade\s*point(?:\s*average)?)\s*[:\-]?\s*(\d+\.\d+)"
    r"(?:\s*/\s*(\d+(?:\.\d+)?))?",
    re.I,
)

DEGREE_KEYWORDS = re.compile(
    r"\b(b\.?s\.?c?\.?|b\.?e\.?|b\.?tech\.?|m\.?s\.?c?\.?|m\.?e\.?|m\.?tech\.?|"
    r"b\.?sc\.?|m\.?sc\.?|ph\.?d\.?|bachelor[s]?|master[s]?|doctor(?:ate)?|associate|"
    r"diploma|bs|ms|be|btech|mtech|mba|bba|bca|mca|b\.?com|m\.?com|hnd|hnc)\b",
    re.I,
)

_INSTITUTION_KW = re.compile(
    r"\b(university|college|school|institute|academy|polytechnic|"
    r"iit|nust|air|lums|fast|comsats|pu|uet|ntu|mit|stanford|harvard|"
    r"oxford|cambridge|national|international)\b",
    re.I,
)

_CW_INLINE = re.compile(
    r"^(?:relevant|related|key|core|selected|notable)?\s*"
    r"(?:coursework|courses?(?:\s+taken)?|modules?)\s*[:\-]\s*(.+)",
    re.I,
)

_CW_HEADER = re.compile(
    r"^(?:relevant|related|key|core|selected|notable)?\s*"
    r"(?:coursework|courses?(?:\s+taken)?|modules?)\s*[:\-]?\s*$",
    re.I,
)


# ============================================================
# SKILL NAME NORMALIZATION
# ============================================================

SKILL_NORMALIZATIONS: Dict[str, str] = {
    "numpy": "NumPy",
    "pandas": "Pandas",
    "scipy": "SciPy",
    "matplotlib": "Matplotlib",
    "seaborn": "Seaborn",
    "plotly": "Plotly",
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "scikit_learn": "scikit-learn",
    "tensorflow": "TensorFlow",
    "tf": "TensorFlow",
    "pytorch": "PyTorch",
    "torch": "PyTorch",
    "keras": "Keras",
    "xgboost": "XGBoost",
    "lightgbm": "LightGBM",
    "lgbm": "LightGBM",
    "huggingface": "HuggingFace",
    "hugging face": "HuggingFace",
    "hugging_face": "HuggingFace",
    "hf": "HuggingFace",
    "spacy": "spaCy",
    "nltk": "NLTK",
    "transformers": "Transformers",
    "bert": "BERT",
    "gpt": "GPT",
    "bart": "BART",
    "t5": "T5",
    "langchain": "LangChain",
    "lang chain": "LangChain",
    "llamaindex": "LlamaIndex",
    "llama index": "LlamaIndex",
    "llama_index": "LlamaIndex",
    "openai": "OpenAI API",
    "openai api": "OpenAI API",
    "llm": "LLM",
    "llms": "LLM",
    "rag": "RAG",
    "chainlit": "Chainlit",
    "opencv": "OpenCV",
    "cv2": "OpenCV",
    "yolov8": "YOLOv8",
    "yolo v8": "YOLOv8",
    "esrgan": "ESRGAN",
    "reactjs": "React",
    "react js": "React",
    "react.js": "React",
    "nodejs": "Node.js",
    "node js": "Node.js",
    "node.js": "Node.js",
    "nextjs": "Next.js",
    "next js": "Next.js",
    "expressjs": "Express.js",
    "express js": "Express.js",
    "vuejs": "Vue.js",
    "vue js": "Vue.js",
    "angularjs": "Angular",
    "tailwindcss": "Tailwind CSS",
    "tailwind": "Tailwind CSS",
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "springboot": "Spring Boot",
    "spring boot": "Spring Boot",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "mongo": "MongoDB",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "chromadb": "ChromaDB",
    "pinecone": "Pinecone",
    "weaviate": "Weaviate",
    "aws": "AWS",
    "amazon web services": "AWS",
    "gcp": "GCP",
    "google cloud": "GCP",
    "google cloud platform": "GCP",
    "azure": "Azure",
    "microsoft azure": "Azure",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "terraform": "Terraform",
    "git": "Git",
    "github": "GitHub",
    "gitlab": "GitLab",
    "jupyter": "Jupyter",
    "jupyter notebooks": "Jupyter",
    "jupyter notebook": "Jupyter",
    "vscode": "VS Code",
    "vs code": "VS Code",
    "google data studio": "Google Data Studio",
    "google sheets api": "Google Sheets API",
    "gcp cloud run": "GCP Cloud Run",
    "google cloud run": "GCP Cloud Run",
    "postman": "Postman",
}


def normalize_skill_name(name: str) -> str:
    if not name:
        return name
    key = name.strip().lower()
    return SKILL_NORMALIZATIONS.get(key, name.strip())


# ============================================================
# CANONICAL CATEGORY OVERRIDES
# ============================================================

SKILL_CANONICAL_CATEGORY: Dict[str, str] = {
    "numpy":        "frameworks",
    "pandas":       "frameworks",
    "scipy":        "frameworks",
    "matplotlib":   "frameworks",
    "seaborn":      "frameworks",
    "plotly":       "frameworks",
    "scikit-learn": "frameworks",
    "tensorflow":   "frameworks",
    "pytorch":      "frameworks",
    "keras":        "frameworks",
    "xgboost":      "frameworks",
    "lightgbm":     "frameworks",
    "huggingface":  "frameworks",
    "spacy":        "frameworks",
    "nltk":         "frameworks",
    "transformers": "frameworks",
    "bert":         "frameworks",
    "gpt":          "frameworks",
    "bart":         "frameworks",
    "t5":           "frameworks",
    "langchain":    "frameworks",
    "llamaindex":   "frameworks",
    "openai api":   "frameworks",
    "chainlit":     "frameworks",
    "opencv":       "frameworks",
    "chromadb":     "tools",
    "pinecone":     "tools",
    "weaviate":     "tools",
    "postgresql":   "tools",
    "mongodb":      "tools",
    "redis":        "tools",
    "elasticsearch":"tools",
    "sqlite":       "tools",
    "mysql":        "tools",
    "firebase":     "tools",
    "supabase":     "tools",
    "dynamodb":     "tools",
    "aws":          "tools",
    "gcp":          "tools",
    "azure":        "tools",
    "docker":       "tools",
    "kubernetes":   "tools",
    "terraform":    "tools",
    "ansible":      "tools",
    "jenkins":      "tools",
    "git":          "tools",
    "github":       "tools",
    "gitlab":       "tools",
    "bitbucket":    "tools",
    "jupyter":      "tools",
    "vs code":      "tools",
    "pycharm":      "tools",
    "intellij":     "tools",
    "google data studio": "tools",
    "google sheets api":  "tools",
    "gcp cloud run":      "tools",
    "postman":       "tools",
}


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\(cid:\d+\)", "", text)
    text = re.sub(r"[^\x09\x0A\x0D\x20-\x7E\xA0-\xFF]", "", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"^[\s\-=_*#|~]{3,}$", "", text, flags=re.MULTILINE)
    return text.strip()


def normalize_line(line: str) -> str:
    return re.sub(r"\s{2,}", " ", line.strip())


# ============================================================
# HEADING DETECTION
# ============================================================

def _flex_heading(s: str) -> str:
    s = re.sub(r"\s*[&+/]\s*", " and ", s)
    return re.sub(r"\s+", " ", s).strip()


def is_heading(line: str) -> Optional[str]:
    norm = normalize_line(line)
    norm_clean = norm.lower().strip(" :\u2013\u2014-\t|")
    if not norm_clean or len(norm_clean) > 80:
        return None
    norm_flex = _flex_heading(norm_clean)
    for section, aliases in SECTION_HEADERS.items():
        for alias in aliases:
            alias_flex = _flex_heading(alias)
            if norm_clean == alias or norm_flex == alias_flex:
                return section
            if re.match(rf"^{re.escape(alias)}[\s:\u2013\u2014\-]+", norm_clean):
                return section
            if re.match(rf"^{re.escape(alias_flex)}[\s:\u2013\u2014\-]+", norm_flex):
                return section
    return None


# ============================================================
# CONTACT EXTRACTORS
# ============================================================

def extract_emails(text: str) -> List[str]:
    return list(dict.fromkeys(EMAIL_REGEX.findall(text)))


def _clean_phone(raw: str) -> str:
    s = raw.strip()
    s = re.sub(r"\((\+\d{1,3})\)", r"\1", s)
    s = re.sub(r"[()]", "", s)
    return s.strip()


def extract_phones(text: str) -> List[str]:
    seen: set = set()
    results: List[str] = []
    for m in _PHONE_FULL_RE.finditer(text):
        cleaned = _clean_phone(m.group(1))
        digits = re.sub(r"\D", "", cleaned)
        if 7 <= len(digits) <= 15 and digits not in seen:
            seen.add(digits)
            results.append(cleaned)
    return results


def extract_links(text: str) -> List[str]:
    raw = list(dict.fromkeys(URL_REGEX.findall(text)))
    return [u for u in raw if "@" not in u]


# ============================================================
# LOCATION EXTRACTION (IMPROVED)
# ============================================================

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
    "dubai", "abu dhabi", "sharjah", "doha", "riyadh", "jeddah",
    "damascus", "beirut", "amman", "baghdad", "tehran", "istanbul",
    "kabul", "kuala lumpur", "singapore", "jakarta", "bangkok",
    "manila", "hanoi", "ho chi minh", "seoul", "busan", "tokyo",
    "osaka", "kyoto", "yokohama", "nagoya", "sapporo", "fukuoka",
    "kobe", "beijing", "shanghai", "guangzhou", "shenzhen", "chengdu",
    "hangzhou", "wuhan", "xian", "nanjing", "tianjin", "chongqing",
    "hong kong", "taipei", "kaohsiung", "sao paulo", "rio de janeiro",
    "brasilia", "buenos aires", "santiago", "lima", "bogota", "caracas",
    "ciudad de mexico", "guadalajara", "havana", "berlin", "hamburg",
    "munich", "cologne", "frankfurt", "paris", "marseille", "lyon",
    "toulouse", "nice", "rome", "milan", "naples", "turin", "madrid",
    "barcelona", "valencia", "seville", "amsterdam", "rotterdam",
    "brussels", "antwerp", "zurich", "geneva", "basel", "bern",
    "vienna", "graz", "stockholm", "gothenburg", "malmo", "oslo",
    "bergen", "copenhagen", "aarhus", "helsinki", "espoo", "tampere",
    "warsaw", "krakow", "prague", "brno", "budapest", "debrecen",
    "bucharest", "cluj", "sofia", "plovdiv", "zagreb", "split",
    "belgrade", "novi sad", "ljubljana", "sarajevo", "tirana",
    "athens", "thessaloniki", "nicosia", "limassol", "reykjavik",
    "luxembourg", "monaco", "moscow", "saint petersburg", "kyiv",
    "kharkiv", "minsk", "tbilisi", "yerevan", "baku", "astana",
    "almaty", "tashkent", "nairobi", "mombasa", "lagos", "kano",
    "addis ababa", "mogadishu", "kampala", "kigali", "bujumbura",
    "dar es salaam", "lusaka", "harare", "maputo", "windhoek",
    "gaborone", "maseru", "mbabane", "cairo", "alexandria", "casablanca",
    "tunis", "algiers", "tripoli", "khartoum", "juba", "asmara",
    "djibouti", "pretoria", "cape town", "durban", "johannesburg",
    "luanda", "kinshasa", "brazzaville", "libreville", "malabo",
    "yaounde", "douala", "bangui", "ndjamena", "niamey", "ouagadougou",
    "bamako", "conakry", "freetown", "monrovia", "yamoussoukro",
    "abidjan", "accra", "kumasi", "lome", "porto-novo", "abuja",
}

_STATE_ABBREVS = {
    "al", "ak", "az", "ar", "ca", "co", "ct", "de", "fl", "ga",
    "hi", "id", "il", "in", "ia", "ks", "ky", "la", "me", "md",
    "ma", "mi", "mn", "ms", "mo", "mt", "ne", "nv", "nh", "nj",
    "nm", "ny", "nc", "nd", "oh", "ok", "or", "pa", "ri", "sc",
    "sd", "tn", "tx", "ut", "vt", "va", "wa", "wv", "wi", "wy",
    "dc", "pr", "vi", "gu", "mp", "as",
    "ab", "bc", "mb", "nb", "nl", "ns", "nt", "nu", "on", "pe",
    "qc", "sk", "yt",
}

_LOCATION_COUNTRY_RE = re.compile(
    r"\b(pakistan|india|bangladesh|nepal|sri\s+lanka|"
    r"united\s+states|united\s+kingdom|usa|uk|uae|canada|"
    r"australia|germany|france|china|japan|singapore|"
    r"new\s+zealand|south\s+africa|nigeria|kenya|remote|hybrid)\b",
    re.I,
)


def extract_location(text: str) -> Optional[str]:
    lines = text.split("\n")[:20]
    candidates = []

    for line in lines:
        lc = line.strip()
        if not lc:
            continue

        lc = EMAIL_REGEX.sub(" ", lc)
        lc = URL_REGEX.sub(" ", lc)
        lc = re.sub(r"\+?\d[\d\s\-()\.]{7,}", " ", lc)
        lc = re.sub(r"\s{2,}", " ", lc).strip()

        if not lc or len(lc) > 60:
            continue

        city_country_match = re.search(
            r"(?:^|(?<=[\s|,]))"
            r"([A-Z][a-zA-Z\-]{1,25}(?:\s+[A-Z][a-zA-Z\-]{1,25}){0,2})"
            r",\s*"
            r"([A-Z][a-zA-Z\-]{1,25}(?:\s+[A-Z][a-zA-Z\-]{1,25})?|[A-Z]{2})"
            r"(?=[\s|;,]|$)",
            lc,
        )

        if city_country_match:
            city = city_country_match.group(1).strip()
            region = city_country_match.group(2).strip()

            if (
                not DEGREE_KEYWORDS.search(city)
                and not DEGREE_KEYWORDS.search(region)
                and not _INSTITUTION_KW.search(city)
                and len(city.split()) <= 4
            ):
                city_lower = city.lower()
                region_lower = region.lower()

                is_known_city = city_lower in _COMMON_CITIES
                is_known_country = region_lower in _VALID_COUNTRIES
                is_state_abbrev = region_lower in _STATE_ABBREVS

                if is_known_city or is_known_country or is_state_abbrev:
                    candidates.append(f"{city}, {region}")
                    continue

        country_match = _LOCATION_COUNTRY_RE.search(lc)
        if country_match:
            country = country_match.group(0).title()
            if not _INSTITUTION_KW.search(lc):
                candidates.append(country)
                continue

        for city in _COMMON_CITIES:
            pattern = rf"\b{re.escape(city)}\b"
            if re.search(pattern, lc, re.I):
                if not _INSTITUTION_KW.search(lc):
                    candidates.append(city.title())
                    break

        if re.search(r"\bRemote\b", lc, re.I):
            candidates.append("Remote")
            continue
        if re.search(r"\bHybrid\b", lc, re.I):
            candidates.append("Hybrid")
            continue

    if candidates:
        comma_candidates = [c for c in candidates if "," in c]
        if comma_candidates:
            return comma_candidates[0]
        return candidates[0]

    return None


# ============================================================
# NAME FALLBACK
# ============================================================

_NON_NAME_PATTERNS = re.compile(
    r"(?:resume|cv|curriculum|vitae|portfolio|profile|contact|phone|email|"
    r"address|linkedin|github|objective|summary|education|experience|skills|"
    r"university|college|engineer|developer|manager|analyst|intern|"
    r"bachelor|master|bsc|msc|btech|mtech|gpa|cgpa|@|http|www\.)",
    re.I,
)


def extract_name_fallback(text: str) -> Optional[str]:
    lines = [l.strip() for l in text.split("\n")[:10] if l.strip()]
    for line in lines:
        if "@" in line or re.search(r"\d", line):
            continue
        if URL_REGEX.search(line):
            continue
        if is_heading(line):
            continue
        if _NON_NAME_PATTERNS.search(line):
            continue
        words = line.split()
        if 2 <= len(words) <= 4:
            alpha_words = [w for w in words if re.match(r"^[A-Za-z\-\'\.]+$", w)]
            if len(alpha_words) == len(words):
                cap_count = sum(1 for w in alpha_words if w[0].isupper())
                if cap_count / len(alpha_words) >= 0.75:
                    joined = " ".join(alpha_words).lower()
                    if not _NON_NAME_PATTERNS.search(joined):
                        return line
    return None


# ============================================================
# SUMMARY CLEANER
# ============================================================
# Words that look like proper names (capital first letter) but are NOT names.
# Used to prevent stripping "Engineer With Python experience…" etc.
import re

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
URL_REGEX = re.compile(r"https?://\S+|www\.\S+")

# ── Tokens that look like proper names (Capital+lowercase) but are NOT ────────
_NOT_A_NAME_TOKEN = re.compile(
    r"^(?:"
    # Common English function / connector words
    r"With|In|At|For|From|The|An|A|Of|And|Or|But|As|By|To|On|Over|"
    r"Is|Are|Was|Were|Has|Have|Had|Who|Which|That|This|These|Those|My|"
    r"Seeking|Looking|Working|Helping|Building|Creating|Developing|"
    # Resume opener adjectives
    r"Experienced|Skilled|Dedicated|Passionate|Motivated|Accomplished|"
    r"Proficient|Creative|Innovative|Dynamic|Versatile|Aspiring|Recent|"
    # ── KEY ADDITION: academic / tech / field nouns ───────────────────────────
    # These all start Capital+lowercase and would be mistaken for name tokens
    r"Computer|Engineering|Software|Machine|Learning|Data|Science|"
    r"Web|Mobile|Cloud|Network|Systems?|Business|Technical|Information|"
    r"Technology|Graduate|Bachelor|Master|Doctor|University|College|"
    r"Institute|Management|Research|Analysis|Development|Design|"
    r"Architecture|Security|Database|Artificial|Intelligence|Vision|"
    r"Language|Processing|Framework|Platform|Application|Service|"
    r"Product|Project|Solutions?"
    r")$",
    re.I,
)

_SUMMARY_OPENERS = re.compile(
    r"^(?:i\s+(?:am|have)|experienced|skilled|passionate|dedicated|motivated|"
    r"results[\-\s]driven|dynamic|versatile|accomplished|proficient|creative|"
    r"innovative|computer|software|data|machine|artificial|web|mobile|cloud|"
    r"full[\-\s]?stack|front[\-\s]?end|back[\-\s]?end|recent|fresh|aspiring|"
    r"graduate|student|professional|engineer|developer|analyst|designer|"
    r"with\s+\d|\d+[\+]?\s*years?|over\s+\d)",
    re.I,
)

_TITLE_MODS = (
    r"(?:(?:[Ss]enior|[Jj]unior|[Ll]ead|[Ss]taff|[Pp]rincipal|[Cc]hief|[Hh]ead|"
    r"[Ff]ull[\s\-]?[Ss]tack|[Ff]ront[\s\-]?[Ee]nd|[Bb]ack[\s\-]?[Ee]nd|"
    r"[Ss]oftware|[Dd]ata|[Mm]obile|[Cc]loud|[Cc]omputer|[Ww]eb)\s+)*"
)

_TITLE_WORDS = (
    r"(?:[Ee]ngineer|[Dd]eveloper|[Aa]nalyst|[Mm]anager|[Ii]ntern|[Dd]esigner|"
    r"[Cc]onsultant|[Aa]rchitect|[Rr]esearcher|[Ss]cientist|[Pp]rogrammer|"
    r"[Ss]pecialist|[Oo]fficer|[Ee]xecutive|[Dd]irector|[Tt]echnologist)"
)


def _is_noise_prefix(prefix: str) -> bool:
    """True when text before matched sentence has no readable lowercase words."""
    return not bool(re.search(r'\b[a-z]{3,}\b', prefix))


def _strip_title_name_prefix(text: str) -> str:
    """
    Remove a leading 'JobTitle PersonName(s)' fragment using token-by-token
    scanning instead of a greedy regex — stops the moment it hits a field
    word like 'Computer' or 'Engineering'.

    ✓  "Engineer Rafia Computer Engineering graduate…"
            → "Computer Engineering graduate…"
    ✓  "Senior Developer John Smith with 5 years…"
            → "with 5 years…"   (capitalised by step 7b)
    ✗  "Engineer With Python experience…"   → unchanged (no name tokens)
    ✗  "Computer Engineering graduate…"     → unchanged (no title match)
    """
    title_m = re.match(rf"^{_TITLE_MODS}{_TITLE_WORDS}\s*", text)
    if not title_m:
        return text

    rest = text[title_m.end():]
    tokens = rest.split()
    chars_consumed = 0
    name_count = 0

    for tok in tokens:
        clean = re.sub(r"[,.\-']+$", "", tok)          # strip trailing punctuation
        if (re.match(r"^[A-Z][a-z]{1,25}$", clean)     # looks like a name token
                and not _NOT_A_NAME_TOKEN.match(clean)  # is not a field/common word
                and name_count < 3):                    # at most 3 name tokens
            name_count += 1
            chars_consumed += len(tok) + 1              # +1 for the space
        else:
            break

    if name_count == 0:
        return text  # nothing to strip

    return text[title_m.end() + chars_consumed:].strip()


def _strip_bare_name_prefix(text: str) -> str:
    """Remove a bare 'Firstname Lastname' prefix when the body is a real summary."""
    m = re.match(r"^([A-Z][a-z]{1,20}(?:\s+[A-Z][a-z]{1,20}){0,3})\s+(?=\w)", text)
    if not m:
        return text

    tokens = m.group(1).split()
    if not all(
        re.match(r"^[A-Z][a-z]{1,20}$", tok) and not _NOT_A_NAME_TOKEN.match(tok)
        for tok in tokens
    ):
        return text

    remainder = text[m.end():]
    if _SUMMARY_OPENERS.match(remainder) or re.match(r"^[a-z]", remainder):
        return remainder.strip()

    return text


def clean_summary(text: str) -> str:
    if not text:
        return ""

    # ── 1. Remove contact artefacts ──────────────────────────────────────────
    text = EMAIL_REGEX.sub("", text)
    text = URL_REGEX.sub("", text)
    text = re.sub(r"\+?\d[\d\s\-()\.]{7,}", "", text)

    # ── 2. Normalise special / non-latin characters ───────────────────────────
    text = re.sub(r"[|#\u2022\u25cf\u25e6\u2023\u2043\uf0b7\u00b7]+", " ", text)
    text = re.sub(
        r"[\u00f0\u00d0\u00fe\u00de\u00f8\u00d8\u00a2\u00a3"
        r"\u00a5\u00a7\u00a9\u00ae\u00b0\u00b1\u00b2\u00b3"
        r"\u00b5\u00b6\u00d7\u00f7]+",
        " ", text,
    )
    text = re.sub(r"[^\x20-\x7E\xA0-\xFF]", " ", text)

    # ── 3. Strip leading parentheticals / pre-capital noise ───────────────────
    text = re.sub(r"^\s*\([^)]{0,150}\)\s*", "", text)
    text = re.sub(r"^\s*\(?[^A-Z.]{0,80}(?=[A-Z])", "", text)

    # ── 4. Remove inline name / location / all-caps fragments ─────────────────
    text = re.sub(
        r"(?:^|(?<=\s))[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?,\s*"
        r"(?:[A-Z][a-z]+|[A-Z]{2,3})(?=\s|$)",
        " ", text,
    )
    text = re.sub(r"(?:^|(?<=\s))(?:[A-Z]{2,}(?:\s+[A-Z]{2,}){1,4})(?=\s|$)", " ", text)
    text = re.sub(r"(?:^|(?<=\s))[+|()\-_@]+(?=\s|$)", " ", text)
    text = re.sub(r"\s{2,}", " ", text).strip().strip(" ,;:+()")

    # ── 5. Strip "JobTitle PersonName(s)" prefix (token-by-token) ─────────────
    text = _strip_title_name_prefix(text)

    # ── 6. Strip legacy title + lowercase-word prefix ─────────────────────────
    text = re.sub(
        r"^(?:(?:[Ss]enior|[Jj]unior|[Ll]ead|[Ss]taff|[Pp]rincipal)\s+)?"
        r"(?:[Ee]ngineer|[Dd]eveloper|[Aa]nalyst|[Mm]anager|[Ii]ntern|"
        r"[Dd]esigner|[Cc]onsultant|[Aa]rchitect|[Rr]esearcher|[Ss]cientist|"
        r"[Pp]rogrammer|[Ss]pecialist|[Oo]fficer|[Ee]xecutive)\s+"
        r"(?:[a-z][a-zA-Z]*\s+){1,3}",
        "", text,
    ).strip()

    text = re.sub(r"\s{2,}", " ", text).strip().strip(" ,;:+()")

    # ── 7. Strip bare "Firstname Lastname" prefix ─────────────────────────────
    text = _strip_bare_name_prefix(text)

    # ── 7b. Capitalise if stripping left a lowercase opener ───────────────────
    # e.g. stripping "Engineer John" from "Engineer John specializing in ML…"
    # leaves "specializing…" — capitalise so step 8 doesn't skip into it.
    if text and text[0].islower():
        text = text[0].upper() + text[1:]

    text = re.sub(r"\s{2,}", " ", text).strip().strip(" ,;:+()")

    # ── 8. Advance to first real summary sentence ─────────────────────────────
    # Guard: only skip forward when the prefix is pure noise (no lowercase words).
    # "specializing in Machine Learning" is NOT noise — do not skip.
    m = re.search(r"(?:^|(?<=\s))([A-Z][a-z]{2,}(?:\s+[\w,\.\-\']+){4,})", text)
    if m:
        matched_text = m.group(1)
        prefix = text[:m.start()]
        if _is_noise_prefix(prefix) and (m.start() > 2 or _SUMMARY_OPENERS.match(matched_text)):
            text = text[m.start():].strip()

    return text.strip(" ,;:+()")

# ============================================================
# DATE EXTRACTION
# ============================================================

def extract_date_range(text: str) -> Optional[Dict]:
    m = DATE_RANGE_REGEX.search(text)
    if not m:
        return None

    def _year(v: str) -> Optional[int]:
        y = re.search(r"\d{4}", v)
        if not y:
            y2 = re.search(r"'(\d{2})\b", v)
            if y2:
                return 2000 + int(y2.group(1))
        return int(y.group()) if y else None

    end_str = m.group("end")
    is_current = end_str.lower() in {"present", "current", "now", "ongoing"}

    return {
        "duration":   m.group(0).strip(),
        "start_year": _year(m.group("start")),
        "end_year":   None if is_current else _year(end_str),
        "is_current": is_current,
    }


def extract_single_date(text: str) -> Optional[str]:
    m = DATE_SINGLE_REGEX.search(text)
    if m:
        return m.group(0).strip()
    m2 = DATE_YEAR_ONLY_REGEX.search(text)
    return m2.group(1) if m2 else None


# ============================================================
# EXPERIENCE PARSING
# ============================================================

_LOCATION_COUNTRIES = {
    "pakistan", "india", "usa", "uk", "us", "canada", "australia",
    "germany", "france", "china", "japan", "united states",
    "united kingdom", "singapore", "uae", "remote", "hybrid",
}

_JOB_TITLE_WORDS = {
    "engineer", "developer", "analyst", "manager", "intern",
    "designer", "consultant", "architect", "lead", "director",
    "officer", "specialist", "associate", "coordinator",
    "administrator", "researcher", "scientist", "executive",
    "head", "senior", "junior", "staff", "trainee", "apprentice",
    "technician", "supervisor", "vp", "president", "founder",
    "co-founder", "cto", "ceo", "cfo", "principal",
}


def _classify_exp_line(line: str) -> str:
    stripped = line.strip()
    if not stripped:
        return "empty"
    if extract_date_range(stripped):
        return "date"
    if re.match(r"^[\u2022\-\*\u25e6\u25aa\u25cf]\s+", stripped):
        return "bullet"

    words = stripped.split()
    word_set = {w.lower().strip(".,()") for w in words}

    if LOCATION_REGEX.match(stripped):
        if any(w in _LOCATION_COUNTRIES for w in [w.lower().strip(".,") for w in words]):
            return "location"
        if len(words) <= 5:
            return "location"

    if (
        1 <= len(words) <= 10
        and not re.search(r"\d{4}", stripped)
        and word_set & _JOB_TITLE_WORDS
    ):
        return "title"

    if len(words) <= 8 and not re.search(r"\d{4}", stripped):
        return "company_or_title"

    return "description"


def parse_experience_section(lines: List[str]) -> List[Dict]:
    entries: List[Dict] = []

    def _make() -> Dict:
        return {
            "role": "", "company": "", "duration": "",
            "start_year": None, "end_year": None,
            "is_current": False, "responsibilities": [],
        }

    current: Optional[Dict] = None
    prev_kind = "empty"

    def _flush():
        nonlocal current
        if current and (current["role"] or current["company"]):
            entries.append(current)
        current = None

    for raw in lines:
        line = raw.strip()
        if not line:
            continue

        sep_m = re.match(r"^(.+?)\s*(?:\|{1,2}|@|at\s+)\s*(.+)$", line)
        if sep_m:
            pa, pb = sep_m.group(1).strip(), sep_m.group(2).strip()
            a_words = {w.lower().strip(".,()") for w in pa.split()}
            if (
                bool(a_words & _JOB_TITLE_WORDS)
                and not re.search(r"\d{4}", pb)
                and not extract_date_range(pb)
            ):
                _flush()
                current = _make()
                current["role"] = pa
                current["company"] = pb
                prev_kind = "title"
                continue

        kind = _classify_exp_line(line)

        if kind == "date":
            di = extract_date_range(line)
            if di and current:
                current["duration"]   = di["duration"]
                current["start_year"] = di["start_year"]
                current["end_year"]   = di["end_year"]
                current["is_current"] = di.get("is_current", False)
            prev_kind = "date"; continue

        if kind == "location":
            prev_kind = "location"; continue

        if kind == "title":
            _flush()
            current = _make()
            current["role"] = re.sub(
                r"\s*\((?:Remote|Hybrid|On-?site)\)\s*", "", line, flags=re.I
            ).strip()
            prev_kind = "title"; continue

        if kind == "company_or_title":
            if current is None:
                current = _make(); current["role"] = line
            elif not current["role"]:
                current["role"] = line
            elif not current["company"] and prev_kind in ("title", "location", "date", "empty"):
                current["company"] = line
            else:
                word_set = {w.lower().strip(".,()") for w in line.split()}
                if word_set & _JOB_TITLE_WORDS and not current.get("duration"):
                    _flush(); current = _make(); current["role"] = line
                else:
                    current["responsibilities"].append(re.sub(r"^[\u2022\-\*\u25e6\u25aa\u25cf]\s*", "", line))
            prev_kind = "company_or_title"; continue

        if kind in ("bullet", "description"):
            if current is None:
                current = _make()
            current["responsibilities"].append(re.sub(r"^[\u2022\-\*\u25e6\u25aa\u25cf]\s*", "", line))
            prev_kind = kind; continue

    _flush()
    return [e for e in entries if e["role"] or e["company"]]


def validate_llm_experience(exp_list: List) -> List[Dict]:
    if not isinstance(exp_list, list):
        return []
    cleaned = []
    for item in exp_list:
        if not isinstance(item, dict):
            continue
        role    = str(item.get("role", "") or "").strip()
        company = str(item.get("company", "") or "").strip()
        if not role and not company:
            continue
        if role and LOCATION_REGEX.match(role):
            continue
        if role.lower() in {"remote", "present", "current"}:
            continue
        responsibilities = item.get("responsibilities", [])
        if isinstance(responsibilities, list):
            responsibilities = [
                str(r).strip() for r in responsibilities
                if str(r).strip() and not LOCATION_REGEX.match(str(r).strip())
            ]
        duration = str(item.get("duration", "") or "").strip()
        di = extract_date_range(duration) if duration else None
        cleaned.append({
            "role": role, "company": company, "duration": duration,
            "start_year": di["start_year"] if di else item.get("start_year"),
            "end_year":   di["end_year"]   if di else item.get("end_year"),
            "is_current": di.get("is_current", False) if di else False,
            "responsibilities": responsibilities,
        })
    return cleaned

from datetime import datetime
from typing import List, Dict, Optional, Tuple


def calculate_total_experience(entries: List[Dict]) -> Dict:
    """
    Calculate total work experience from parsed experience entries.
    Handles overlapping jobs (e.g. freelance + full-time simultaneously).
    
    Returns:
        {
            "total_years": 5,
            "total_months": 2,
            "total_months_raw": 62,
            "display": "5 years 2 months"
        }
    """
    current_year = datetime.now().year
    current_month = datetime.now().month

    # ── 1. Build (start, end) month-precision intervals ───────────────────────
    intervals: List[Tuple[int, int]] = []   # (start_month_abs, end_month_abs)
    # "absolute month" = year * 12 + month  (e.g. Jan 2020 = 2020*12+1 = 24241)

    for entry in entries:
        start_year = entry.get("start_year")
        end_year   = entry.get("end_year")
        is_current = entry.get("is_current", False)

        if not start_year:
            continue  # can't use this entry without a start

        # Try to extract month precision from duration string
        start_month, end_month_val = _parse_month_from_duration(
            entry.get("duration", ""), start_year, end_year
        )

        start_abs = start_year * 12 + start_month

        if is_current or not end_year:
            end_abs = current_year * 12 + current_month
        else:
            end_abs = end_year * 12 + end_month_val

        if end_abs >= start_abs:
            intervals.append((start_abs, end_abs))

    if not intervals:
        return {"total_years": 0, "total_months": 0, "total_months_raw": 0, "display": "N/A"}

    # ── 2. Merge overlapping intervals ────────────────────────────────────────
    #
    #  Job A: |-------|
    #  Job B:     |--------|
    #  Merged:|------------|   ← counted once, not double-counted
    #
    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]

    for start, end in intervals[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:                       # overlapping or touching
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))

    # ── 3. Sum merged intervals ───────────────────────────────────────────────
    total_months_raw = sum(end - start for start, end in merged)

    total_years  = total_months_raw // 12
    total_months = total_months_raw % 12

    # ── 4. Build display string ───────────────────────────────────────────────
    if total_years and total_months:
        display = f"{total_years} year{'s' if total_years != 1 else ''} {total_months} month{'s' if total_months != 1 else ''}"
    elif total_years:
        display = f"{total_years} year{'s' if total_years != 1 else ''}"
    elif total_months:
        display = f"{total_months} month{'s' if total_months != 1 else ''}"
    else:
        display = "Less than a month"

    return {
        "total_years":      total_years,
        "total_months":     total_months,
        "total_months_raw": total_months_raw,
        "display":          display,
    }


def _parse_month_from_duration(
    duration: str,
    start_year: int,
    end_year: Optional[int],
) -> Tuple[int, int]:
    """
    Extract start/end month numbers from a duration string.
    Falls back to January(1) / December(12) if months can't be parsed.
    
    e.g. "Jan 2022 – Mar 2024" → (1, 3)
         "2020 - 2022"         → (1, 12)   ← fallback
    """
    MONTHS = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4,
        "may": 5, "jun": 6, "jul": 7, "aug": 8,
        "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    }

    found = re.findall(
        r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*",
        duration.lower()
    )

    start_month = MONTHS.get(found[0], 1) if len(found) > 0 else 1
    end_month   = MONTHS.get(found[1], 12) if len(found) > 1 else 12

    return start_month, end_month

# ============================================================
# EDUCATION PARSING
# ============================================================

def parse_education_section(lines: List[str]) -> List[Dict]:
    entries: List[Dict] = []

    def _make() -> Dict:
        return {
            "institution": "", "degree": "", "field": "",
            "start_year": None, "end_year": None, "duration": "",
            "gpa": None, "coursework": [],
        }

    current: Optional[Dict] = None
    in_coursework: bool = False

    def _flush():
        nonlocal current, in_coursework
        if current and (current["institution"] or current["degree"]):
            entries.append(current)
        current = None
        in_coursework = False

    def _add_courses(edu: Dict, raw: str) -> None:
        cleaned = re.sub(r"^[\u2022\-\*\u25e6\u25aa\u25cf]\s*", "", raw.strip())
        parts = re.split(r"[,;|]", cleaned)
        edu["coursework"].extend(c.strip() for c in parts if c.strip())

    for raw in lines:
        line = raw.strip()

        if not line:
            in_coursework = False
            continue

        cw_inline = _CW_INLINE.match(line)
        if cw_inline:
            if current:
                _add_courses(current, cw_inline.group(1))
            in_coursework = False
            continue

        if _CW_HEADER.match(line):
            in_coursework = True
            continue

        if in_coursework:
            if (
                DEGREE_KEYWORDS.search(line)
                or _INSTITUTION_KW.search(line)
                or extract_date_range(line)
                or GPA_REGEX.search(line)
            ):
                in_coursework = False
            else:
                if current:
                    _add_courses(current, line)
                continue

        gpa_m = GPA_REGEX.search(line)
        if gpa_m and current:
            current["gpa"] = gpa_m.group(1)
            continue

        di = extract_date_range(line)
        if di:
            if current:
                current["duration"]   = di["duration"]
                current["start_year"] = di["start_year"]
                current["end_year"]   = di["end_year"]
            continue

        if "," in line and not gpa_m:
            _parts = line.split(",", 1)
            _left, _right = _parts[0].strip(), _parts[1].strip()
            if (
                _INSTITUTION_KW.search(_left)
                and DEGREE_KEYWORDS.search(_right)
                and not DEGREE_KEYWORDS.search(_left)
            ):
                if current and current["institution"]:
                    _flush()
                if current is None:
                    current = _make()
                current["institution"] = _left
                dm2 = re.match(
                    r"(b\.?s\.?c?|b\.?e\.?|b\.?tech|m\.?s\.?c?|m\.?e\.?|m\.?tech|"
                    r"bachelor[s]?|master[s]?|ph\.?d|mba|bca|mca|b\.?com|m\.?com|"
                    r"diploma|associate)\s+(?:of\s+|in\s+)?(.*)",
                    _right.strip(), re.I,
                )
                if dm2:
                    current["degree"] = dm2.group(1).strip().upper()
                    current["field"]  = re.sub(r"\s*[-\u2013|,]\s*.*$", "", dm2.group(2)).strip()
                else:
                    current["degree"] = _right
                continue

        if DEGREE_KEYWORDS.search(line):
            if current and current["institution"] and current["degree"]:
                _flush(); current = _make()
            if current is None:
                current = _make()
            dm = re.match(
                r"(b\.?s\.?c?|b\.?e\.?|b\.?tech|m\.?s\.?c?|m\.?e\.?|m\.?tech|"
                r"bachelor[s]?|master[s]?|ph\.?d|mba|bca|mca|b\.?com|m\.?com|"
                r"diploma|associate)\s+(?:of\s+|in\s+)?(.*)",
                line.strip(), re.I,
            )
            if dm:
                current["degree"] = dm.group(1).strip().upper()
                current["field"]  = re.sub(r"\s*[-\u2013|,]\s*.*$", "", dm.group(2)).strip()
            else:
                current["degree"] = line
            continue

        if _INSTITUTION_KW.search(line):
            if current and current["institution"]:
                _flush()
            if current is None:
                current = _make()
            current["institution"] = line
            continue

        if current and current["institution"] and not current["degree"] and len(line.split()) <= 12:
            current["degree"] = line
            continue

        if current is None and len(line.split()) >= 2:
            current = _make()
            current["institution"] = line

    _flush()
    return entries


# ============================================================
# CERTIFICATIONS PARSING (IMPROVED)
# ============================================================

_CERT_NAME_KW = re.compile(
    r"\b(certified|certification|certificate|professional|associate|"
    r"specialist|nanodegree|specialization|course|program|foundation|"
    r"expert|practitioner|introduction|fundamentals|essentials|"
    r"advanced|beginner|developer|engineer|architect)\b",
    re.I,
)

_KNOWN_ISSUERS = re.compile(
    r"^(google|amazon|aws|microsoft|coursera|udemy|linkedin|edx|"
    r"pluralsight|datacamp|codecademy|ibm|cisco|oracle|meta|"
    r"deeplearning\.ai|fast\.ai|kaggle|mongodb|red\s+hat|"
    r"hashicorp|terraform|kubernetes|cncf|comptia|isc2|ec-council|"
    r"offensive\s+security|salesforce|adobe|autodesk|pmi|scrum|"
    r"itil|togaf)$",
    re.I,
)

_CERT_BLACKLIST = re.compile(
    r"\b(communication|leadership|teamwork|problem\s?solving|adaptability|"
    r"time\s?management|critical\s?thinking|collaboration|workshop|"
    r"hackathon|bootcamp|seminar|webinar|training\s+course|class|"
    r"volunteering|membership|society|club|honor|dean|soft\s?skill|"
    r"interpersonal|negotiation|presentation|conflict\s?resolution|"
    r"decision\s?making|strategic\s?thinking|empathy|mentoring|coaching|"
    r"self-motivated|proactive|initiative|fast\s?learner|quick\s?learner|"
    r"creativity|innovation|adaptability|flexible|versatile|organized|"
    r"multitasking|prioritization|detail\s?oriented|work\s?ethic|reliable|"
    r"dependable|hardworking)\b",
    re.I,
)

_QUOTE_CHARS = re.compile(r'^["\u201c\u201d\u2018\u2019]+|["\u201c\u201d\u2018\u2019]+$')


def _strip_quotes(s: str) -> str:
    return _QUOTE_CHARS.sub("", s).strip(" .")


def _is_continuation(line: str, prev_name: str) -> bool:
    line_lower = line.lower().strip()
    if re.match(r"^(and|or|&)\b", line_lower):
        return True
    if prev_name.rstrip().endswith(","):
        words = line.split()
        if (
            len(words) <= 6
            and not extract_date_range(line)
            and not extract_single_date(line)
            and not _KNOWN_ISSUERS.match(line.strip())
        ):
            return True
    return False


def _is_valid_certification(name: str, issuer: Optional[str] = None) -> bool:
    if not name or len(name) < 3:
        return False

    name_lower = name.lower()

    if _CERT_BLACKLIST.search(name):
        return False

    has_cert_kw = bool(_CERT_NAME_KW.search(name))
    has_known_issuer = False
    if issuer:
        has_known_issuer = bool(_KNOWN_ISSUERS.match(issuer.strip()))

    if not (has_cert_kw or has_known_issuer):
        return False

    if not issuer and not has_cert_kw:
        return False

    return True


def parse_certifications_section(lines: List[str]) -> List[Dict]:
    entries: List[Dict] = []
    current: Optional[Dict] = None

    def _flush():
        nonlocal current
        if current and current.get("name"):
            current["name"] = _strip_quotes(current["name"]).rstrip(".")
            if _is_valid_certification(current["name"], current.get("issuer")):
                entries.append(current)
        current = None

    def _new(name: str) -> Dict:
        return {
            "name": _strip_quotes(name).rstrip("."),
            "issuer": None, "date": None,
            "credential_id": None, "url": None,
        }

    def _assign_extra(cert: Dict, part: str) -> None:
        part = part.strip()
        if not part:
            return
        di = extract_date_range(part)
        sd = extract_single_date(part)
        if di:
            cert["date"] = di["duration"]
        elif sd and len(part) <= len(sd) + 5:
            cert["date"] = part
        elif re.match(r"^(19|20)\d{2}$", part):
            cert["date"] = part
        elif URL_REGEX.search(part):
            cert["url"] = URL_REGEX.search(part).group(0)
        elif cert["issuer"] is None:
            cert["issuer"] = part
        else:
            cert["credential_id"] = part

    for raw in lines:
        line = raw.strip()
        if not line:
            continue

        clean = re.sub(r"^[\d]+[.)]\s*|^[\u2022\-\*\u25e6\u25aa\u25cf]\s*", "", line).strip()
        if not clean:
            continue

        if current is not None and _is_continuation(clean, current["name"]):
            current["name"] = current["name"].rstrip(",") + ", " + _strip_quotes(clean).rstrip(".")
            continue

        cid_m = re.match(
            r"(?:credential(?:\s+id)?|certificate\s+(?:no|number)|"
            r"verify(?:\s+at)?|cert(?:ificate)?\s+id)\s*[:\-]?\s*(.+)",
            clean, re.I,
        )
        if cid_m and current:
            val = cid_m.group(1).strip()
            url_m = URL_REGEX.search(val)
            if url_m:
                current["url"] = url_m.group(0)
                before = val[:url_m.start()].strip(" :-")
                if before:
                    current["credential_id"] = before
            else:
                current["credential_id"] = val
            continue

        url_m = URL_REGEX.search(clean)
        if url_m and current:
            non_url = clean.replace(url_m.group(0), "").strip(" :-")
            if len(non_url) < 25:
                current["url"] = url_m.group(0)
                if non_url:
                    current["credential_id"] = non_url
                continue

        issuer_m = re.match(
            r"(?:issued\s+by|issuer|by|from|provider|platform|"
            r"organization|offered\s+by)\s*[:\-]?\s*(.+)",
            clean, re.I,
        )
        if issuer_m and current:
            current["issuer"] = issuer_m.group(1).strip()
            continue

        di = extract_date_range(clean)
        if di and current and len(clean.split()) <= 8:
            current["date"] = di["duration"]
            continue
        sd = extract_single_date(clean)
        if sd and current and len(clean.strip()) <= len(sd) + 5:
            current["date"] = sd
            continue

        if (
            current is not None
            and current["issuer"] is None
            and current["date"] is None
            and len(clean.split()) <= 5
            and not re.search(r"\d", clean)
            and not _CERT_NAME_KW.search(clean)
            and "|" not in clean
            and "\u2014" not in clean
        ):
            current["issuer"] = _strip_quotes(clean)
            continue

        parts = re.split(r"\s*[|\u2014\u2013\u00b7]\s*", clean)
        if len(parts) >= 2:
            first_part = parts[0].strip()
            first_words = first_part.split()
            is_short_non_cert = (
                current is not None
                and current["issuer"] is None
                and len(first_words) <= 4
                and not _CERT_NAME_KW.search(first_part)
                and not extract_date_range(first_part)
            )
            if is_short_non_cert:
                current["issuer"] = first_part
                for p in parts[1:]:
                    _assign_extra(current, p)
            else:
                _flush()
                current = _new(first_part)
                for p in parts[1:]:
                    _assign_extra(current, p)
            continue

        inline_yr = re.search(r"\((\d{4})\)\s*$", clean)
        if inline_yr:
            nm = clean[:inline_yr.start()].strip()
            _flush()
            current = _new(nm)
            current["date"] = inline_yr.group(1)
            continue

        by_m = re.match(r"^(.+?)\s+by\s+(.+)$", clean, re.I)
        if by_m:
            name_part   = _strip_quotes(by_m.group(1).strip())
            issuer_part = by_m.group(2).strip()
            if _CERT_NAME_KW.search(name_part) or _QUOTE_CHARS.search(by_m.group(1)):
                _flush()
                current = _new(name_part)
                current["issuer"] = issuer_part
                continue

        di3 = extract_date_range(clean)
        if di3:
            date_m = DATE_RANGE_REGEX.search(clean)
            if date_m:
                name_part = clean[:date_m.start()].strip().rstrip(" ,-")
                _flush()
                current = _new(name_part) if name_part else _new(clean)
                current["date"] = di3["duration"]
                after = clean[date_m.end():].strip(" ,-")
                if after:
                    current["issuer"] = after
                continue

        if "," in clean and len(clean) > 60 and current is None:
            items = [i.strip() for i in clean.split(",") if i.strip()]
            has_conjunction = any(re.match(r"^(and|or|&)\s", i, re.I) for i in items)
            if len(items) >= 2 and not has_conjunction:
                for item in items:
                    yr_m2 = re.search(r"\((\d{4})\)\s*$", item)
                    nm = re.sub(r"\(\d{4}\)\s*$", "", item).strip()
                    if nm and _is_valid_certification(nm):
                        entries.append({
                            "name": _strip_quotes(nm),
                            "issuer": None,
                            "date": yr_m2.group(1) if yr_m2 else None,
                            "credential_id": None, "url": None,
                        })
                continue

        _flush()
        clean_name = _strip_quotes(clean).rstrip(".")
        if not clean_name:
            continue
        current = _new(clean_name)

    _flush()
    return [e for e in entries if e["name"]]


# ============================================================
# PROJECTS PARSING
# ============================================================

_TECH_LABEL = re.compile(
    r"^(?:tech(?:nologies)?(?:\s+used)?|stack|built\s+with|tools?|"
    r"frameworks?|using|languages?|libraries)\s*[:\-]\s*(.+)",
    re.I,
)

_LINK_LABELS = re.compile(
    r"^(?:link|github|demo|live|url|code|source|repo)\s*[:\-]\s*(.+)",
    re.I,
)

_ACTION_VERBS = re.compile(
    r"^(?:designed|built|developed|implemented|created|trained|"
    r"used|leveraged|utilized|achieved|contributed|worked|"
    r"collaborated|managed|led|deployed|integrated|migrated|"
    r"refactored|optimized|maintained|tested|documented|automated|"
    r"performed|conducted|analyzed|researched|produced|delivered|"
    r"established|spearheaded|improved|increased|reduced|applied|"
    r"employed|leveraged|constructed|formulated|launched)\b",
    re.I,
)


def _extract_tech_from_text(text: str, vocab: Dict[str, List[str]]) -> List[str]:
    t = text.lower()
    found = []
    all_skills = [s for items in vocab.values() for s in items]
    for skill in all_skills:
        if skill in ("c", "r"):
            continue
        if " " in skill:
            if skill in t:
                found.append(skill)
        else:
            if re.search(rf"\b{re.escape(skill)}\b", t):
                found.append(skill)
    yolo_m = re.findall(r"\byolo\d*\b", t)
    if yolo_m and "yolo" not in found:
        found.append("yolo")
    return sorted(set(found))


def parse_projects_section(lines: List[str], skill_vocab: Optional[Dict] = None) -> List[Dict]:
    projects: List[Dict] = []
    current: Optional[Dict] = None

    def _flush():
        nonlocal current
        if current and (current["name"] or current["description"]):
            if skill_vocab and not current["tech_stack"] and current["description"]:
                full_desc = " ".join(current["description"])
                auto_tech = _extract_tech_from_text(full_desc, skill_vocab)
                current["tech_stack"] = auto_tech
            projects.append(current)
        current = None

    def _new(name: str) -> Dict:
        return {"name": name.strip(), "description": [], "tech_stack": [], "links": []}

    for raw in lines:
        line = raw.strip()
        if not line:
            continue

        tech_m = _TECH_LABEL.match(line)
        if tech_m:
            techs = [t.strip() for t in re.split(r"[,|;]", tech_m.group(1)) if t.strip()]
            if current:
                current["tech_stack"].extend(techs)
            continue

        link_m = _LINK_LABELS.match(line)
        if link_m:
            url_m = URL_REGEX.search(link_m.group(1))
            if url_m and current:
                current["links"].append(url_m.group(0))
                continue

        url_m = URL_REGEX.search(line)
        if url_m and current:
            non_url = line.replace(url_m.group(0), "").strip(" :-")
            if len(non_url) < 20:
                current["links"].append(url_m.group(0))
                continue

        if re.match(r"^[\u2022\-\*\u25e6\u25aa\u25cf]\s+", line):
            if current is None:
                current = _new("")
            current["description"].append(re.sub(r"^[\u2022\-\*\u25e6\u25aa\u25cf]\s*", "", line))
            continue

        words = line.split()
        is_title = (
            len(words) <= 8
            and not re.match(r"^[\u2022\-\*\u25e6\u25aa\u25cf]", line)
            and line[0].isupper()
            and not line.endswith(",")
            and not re.match(r"^\w+:", line)
            and not _ACTION_VERBS.match(line)
            and not re.search(r"\d+%|\.\d+", line)
        )
        if is_title:
            _flush()
            name = re.sub(r"^(?:project\s*\d*\s*[:\-]\s*)", "", line, flags=re.I).strip()
            current = _new(name)
            continue

        if current:
            current["description"].append(re.sub(r"^[\u2022\-\*\u25e6\u25aa\u25cf]\s*", "", line))
        else:
            current = _new("")
            current["description"].append(line)

    _flush()
    return [p for p in projects if p["name"] or p["description"]]


# ============================================================
# RULE-BASED SKILL VOCABULARY
# ============================================================

SKILL_VOCABULARY: Dict[str, List[str]] = {
    "technical": [
        "machine learning", "deep learning", "computer vision",
        "image processing", "face recognition", "object detection",
        "natural language processing", "nlp", "data mining",
        "neural networks", "reinforcement learning",
        "embedded systems", "iot", "robotics",
        "distributed systems", "microservices", "cloud computing",
        "cybersecurity", "network security", "cryptography",
        "operating systems", "parallel computing",
        "signal processing", "control systems",
        "database design", "system design", "software architecture",
        "agile", "scrum", "devops", "ci/cd",
        "restful api", "rest api", "graphql", "grpc",
        "data structures", "algorithms", "oop",
        "object oriented programming", "functional programming",
        "test driven development", "tdd", "unit testing",
        "version control", "web scraping", "api integration",
        "data pipeline", "etl",
    ],
    "languages": [
        "c", "c++", "c#",
        "python", "javascript", "typescript", "java",
        "go", "rust", "ruby", "php", "swift", "kotlin",
        "scala", "r", "matlab", "sql", "bash", "shell",
        "html", "css", "sass", "scss", "solidity", "dart",
        "perl", "lua", "assembly",
    ],
    "frameworks": [
        "tensorflow", "pytorch", "keras", "scikit-learn", "sklearn",
        "xgboost", "lightgbm",
        "pandas", "numpy", "scipy", "matplotlib", "seaborn", "plotly",
        "huggingface", "langchain", "llamaindex", "transformers",
        "nltk", "spacy",
        "openai", "chainlit",
        "opencv", "pillow",
        "react", "vue", "angular", "next.js", "nextjs",
        "express", "fastapi", "django", "flask", "spring",
        "spring boot", "laravel", "node.js", "nodejs",
        "nest.js", "nestjs", "react native", "flutter",
        "electron", "tailwindcss", "tailwind", "bootstrap",
        "material-ui", "chakra ui",
        "celery", "sqlalchemy", "prisma", "mongoose",
        "junit", "pytest", "jest", "cypress", "playwright",
        "efficientnet", "facenet",
    ],
    "tools": [
        "git", "github", "gitlab", "bitbucket",
        "docker", "kubernetes", "terraform", "ansible",
        "aws", "azure", "gcp", "firebase", "heroku",
        "vercel", "netlify", "digitalocean",
        "jenkins", "github actions", "circleci", "travis ci",
        "postgresql", "mysql", "mongodb", "redis",
        "elasticsearch", "sqlite", "oracle", "mssql",
        "cassandra", "dynamodb", "supabase",
        "chromadb", "pinecone", "weaviate",
        "ffmpeg",
        "yolo",
        "jupyter", "vscode", "intellij", "pycharm",
        "postman", "insomnia",
        "figma", "jira", "confluence", "notion", "slack", "trello",
        "linux", "ubuntu", "windows", "macos",
        "nginx", "apache", "rabbitmq", "kafka",
        "grafana", "prometheus", "sentry", "datadog",
        "google data studio",
        "wordpress", "moodle",
    ],
    "other": [],
}


_SKILL_PATTERN_CACHE: Dict[str, re.Pattern] = {}

def _get_skill_pattern(skill: str) -> re.Pattern:
    if skill not in _SKILL_PATTERN_CACHE:
        escaped = re.escape(skill)
        _SKILL_PATTERN_CACHE[skill] = re.compile(
            rf"(?<![a-zA-Z0-9_]){escaped}(?![a-zA-Z0-9_])",
            re.IGNORECASE,
        )
    return _SKILL_PATTERN_CACHE[skill]

def extract_skills_rule_based(text: str) -> Dict[str, List[str]]:
    t = text.lower()
    found: Dict[str, List[str]] = {cat: [] for cat in SKILL_VOCABULARY}

    for category, vocab in SKILL_VOCABULARY.items():
        for skill in vocab:
            if skill == "r":
                continue

            if skill == "c":
                if re.search(
                    r"(?<![a-zA-Z0-9_])C(?![a-zA-Z0-9_+#])",
                    text,
                ):
                    found[category].append(skill)
                continue

            if " " in skill:
                if skill in t:
                    found[category].append(skill)
                continue

            if _get_skill_pattern(skill).search(t):
                found[category].append(skill)

    if re.search(r"\byolo\d+\b", t) and "yolo" not in found["tools"]:
        found["tools"].append("yolo")

    for cat in found:
        found[cat] = sorted(set(found[cat]))

    return found
