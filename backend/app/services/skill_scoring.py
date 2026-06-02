# app/services/skill_scoring.py
"""
Skill confidence scoring and domain classification.

IMPROVEMENTS:
  ✔ Deterministic confidence scores (0–100) per hard skill
  ✔ Soft skills returned as plain strings — NO scores
  ✔ "other" category suppressed from output
  ✔ Frequency + context proximity weighting
  ✔ Rule-based domain classification with percentage breakdown
  ✔ Improved domain keyword coverage
  ✔ Better C/C++ handling in context bonus
"""

import re
from collections import defaultdict
from typing import Dict, List, Set

# ─────────────────────────────────────────────────────────────
# SOFT SKILLS  (plain strings, never scored)
# ─────────────────────────────────────────────────────────────

SOFT_SKILLS: Set[str] = {
    # Interpersonal
    "communication", "teamwork", "collaboration", "interpersonal skills",
    "active listening", "conflict resolution", "negotiation", "mentoring",
    "coaching", "empathy", "emotional intelligence",
    # Cognitive
    "problem solving", "critical thinking", "analytical thinking",
    "decision making", "attention to detail", "research skills",
    # Leadership / management
    "leadership", "team player", "project management",
    "stakeholder management", "strategic thinking", "delegation",
    "people management",
    # Productivity
    "time management", "multitasking", "prioritization", "organized",
    "self motivation", "self-motivated", "proactive", "initiative",
    "fast learner", "quick learner", "continuous learning",
    # Creative / adaptive
    "creativity", "innovation", "innovative", "adaptability",
    "flexible", "versatile",
    # Communication
    "presentation skills", "public speaking", "technical writing",
    "report writing", "documentation", "detail oriented",
    # Work ethic
    "work ethic", "reliable", "dependable", "hardworking",
}


def extract_soft_skills(text: str) -> List[str]:
    """Return a list of soft skill names found in *text* (no scores)."""
    t = text.lower()
    return sorted(
        skill for skill in SOFT_SKILLS
        if re.search(rf"\b{re.escape(skill)}\b", t)
    )


# ─────────────────────────────────────────────────────────────
# CONFIDENCE SCORING
# ─────────────────────────────────────────────────────────────

_EXP_CTX = re.compile(
    r"(experience|intern|internship|developer|engineer|architect|"
    r"worked|built|implemented|designed|developed|deployed|led|managed|"
    r"created|maintained|optimized|integrated)",
    re.I,
)
_PROJ_CTX = re.compile(
    r"(project|system|application|pipeline|model|tool|platform|"
    r"framework|developed|built|created|implemented|dashboard|service)",
    re.I,
)
_SKILL_SEC_CTX = re.compile(
    r"(skill|technolog|tech\s+stack|tools?|proficient|expertise|"
    r"competenc|libraries|frameworks)",
    re.I,
)


def _count_mentions(skill: str, text: str) -> int:
    if skill == "c++":
        return len(re.findall(r"c\+\+", text))
    if skill == "c#":
        return len(re.findall(r"c#", text))
    if skill == "c":
        return len(re.findall(r"\bc\b(?!\+\+|#|-|ss)", text))
    if " " in skill:
        return text.count(skill)
    try:
        return len(re.findall(rf"\b{re.escape(skill)}\b", text))
    except re.error:
        return text.count(skill)


def _context_bonus(skill: str, text: str) -> int:
    """Return context-based bonus (0–45)."""
    if skill in ("c++", "c#"):
        pat = re.escape(skill)
    elif skill == "c":
        pat = r"\bc\b(?!\+\+|#|-|ss)"
    else:
        pat = re.escape(skill)

    matches = list(re.finditer(pat, text, re.I))
    if not matches:
        return 0

    bonus = 0
    exp_done = proj_done = sec_done = False

    for m in matches:
        s, e = m.start(), m.end()

        if not exp_done:
            w = text[max(0, s - 80): min(len(text), e + 80)]
            if _EXP_CTX.search(w):
                bonus += 20
                exp_done = True

        if not proj_done:
            w = text[max(0, s - 100): min(len(text), e + 100)]
            if _PROJ_CTX.search(w):
                bonus += 15
                proj_done = True

        if not sec_done:
            w = text[max(0, s - 200): s]
            if _SKILL_SEC_CTX.search(w):
                bonus += 10
                sec_done = True

        if exp_done and proj_done and sec_done:
            break

    return bonus


def score_skills(skills: Dict[str, List[str]], full_text: str) -> Dict:
    """
    Build scored skill output.

    Returns a dict of categories → list of {name, confidence}.
    The "other" category is omitted from the output entirely.

    Scoring:
      Base  = min(mentions × 10, 40)
      Bonus = up to 45 from experience / project / skills-section proximity
      Floor = 10  (guaranteed if the skill is present at all)
      Cap   = 100
    """
    text = full_text.lower()
    scored: Dict[str, List[Dict]] = {}

    for category, items in skills.items():
        # Suppress "other"
        if category == "other":
            continue

        bucket: List[Dict] = []
        for skill in items:
            skill_lower = skill.lower()
            mentions = _count_mentions(skill_lower, text)
            if mentions == 0:
                continue
            base  = min(mentions * 10, 40)
            ctx   = _context_bonus(skill_lower, text)
            total = max(min(base + ctx, 100), 10)
            level = (
                "advanced"     if total >= 70 else
                "intermediate" if total >= 45 else
                "beginner"
            )
            bucket.append({"name": skill, "confidence": total, "level": level})

        bucket.sort(key=lambda x: x["confidence"], reverse=True)
        if bucket:
            scored[category] = bucket

    return scored


# ─────────────────────────────────────────────────────────────
# DOMAIN CLASSIFICATION
# ─────────────────────────────────────────────────────────────

DOMAIN_KEYWORDS: Dict[str, List[str]] = {
    "backend": [
        "backend", "back-end", "server", "api", "rest api", "restful",
        "microservices", "graphql", "grpc", "websocket",
        "fastapi", "django", "flask", "node", "express",
        "spring", "spring boot", "laravel", "rails",
        "postgres", "postgresql", "mysql", "mongodb",
        "redis", "database", "sql", "nosql",
        "authentication", "authorization", "middleware",
        "celery", "rabbitmq", "kafka", "redis", "elasticsearch",
        "nginx", "apache", "load balancer", "reverse proxy",
        "oauth", "jwt", "session management", "caching",
    ],
    "frontend": [
        "frontend", "front-end", "ui", "ux", "user interface",
        "user experience", "react", "vue", "angular", "svelte",
        "next.js", "javascript", "typescript",
        "html", "css", "tailwind", "bootstrap",
        "responsive design", "web design", "spa",
        "webpack", "vite", "sass", "scss", "less",
        "material-ui", "chakra ui", "ant design",
        "dom manipulation", "browser", "client-side",
    ],
    "ai_ml": [
        "machine learning", "deep learning", "ai",
        "artificial intelligence", "computer vision",
        "nlp", "natural language processing",
        "pytorch", "tensorflow", "keras", "scikit",
        "neural network", "model training",
        "yolo", "bert", "transformer", "llm",
        "face recognition", "object detection",
        "image classification", "generative ai",
        "langchain", "huggingface", "rag",
        "reinforcement learning", "feature engineering",
        "model deployment", "mlops", "model serving",
        "gan", "vae", "diffusion model", "stable diffusion",
        "openai", "anthropic", "claude", "gpt",
    ],
    "data_science": [
        "data science", "data analysis", "data analytics",
        "pandas", "numpy", "scipy", "matplotlib",
        "sql", "bigquery", "spark", "hadoop",
        "visualization", "statistics", "regression",
        "tableau", "power bi", "looker",
        "etl", "data pipeline", "data warehouse",
        "a/b testing", "hypothesis testing",
        "data engineering", "data modeling",
        "time series", "forecasting", "clustering",
        "classification", "dimensionality reduction",
    ],
    "devops_cloud": [
        "docker", "kubernetes", "k8s", "terraform", "ansible",
        "aws", "azure", "gcp", "cloud", "lambda",
        "ci/cd", "jenkins", "github actions", "circleci",
        "deployment", "infrastructure", "monitoring",
        "prometheus", "grafana", "nginx", "load balancer",
        "devops", "sre", "site reliability",
        "containerization", "orchestration", "helm",
        "vault", "consul", "istio", "linkerd",
        "cloudformation", "pulumi", "serverless",
    ],
    "mobile": [
        "android", "ios", "flutter", "react native",
        "kotlin", "swift", "xamarin", "mobile app",
        "dart", "mobile development", "cordova", "ionic",
        "phonegap", "titanium", "native script",
        "app store", "google play", "apk", "ipa",
        "push notification", "mobile ui", "responsive mobile",
    ],
    "embedded": [
        "embedded", "firmware", "rtos", "arduino",
        "raspberry pi", "microcontroller", "fpga",
        "vhdl", "verilog", "iot", "sensor", "hardware",
        "embedded c", "bare metal", "uart", "spi", "i2c",
        "can bus", "modbus", "ethernet/ip",
        "pcb design", "circuit design", "signal processing",
        "real-time", "interrupt", "dma", "gpio",
    ],
    "security": [
        "cybersecurity", "information security",
        "penetration testing", "pen testing", "ethical hacking",
        "vulnerability", "network security", "cryptography",
        "siem", "soc", "cve", "firewall", "intrusion detection",
        "owasp", "security audit", "threat modeling",
        "compliance", "gdpr", "hipaa", "pci-dss",
        "identity management", "access control", "zero trust",
        "malware analysis", "reverse engineering", "forensics",
    ],
    "full_stack": [
        "full stack", "full-stack", "fullstack",
        "mern", "mean", "lamp", "lemp",
        "backend and frontend", "front-end and back-end",
        "end-to-end", "web development", "web application",
        "crud", "mvc", "mvvm", "restful", "api design",
    ],
    "game_dev": [
        "game development", "game design", "unity", "unreal engine",
        "godot", "game engine", "3d modeling", "blender",
        "game physics", "shader", "opengl", "directx", "vulkan",
        "level design", "game mechanics", "multiplayer",
    ],
    "blockchain": [
        "blockchain", "web3", "smart contract", "solidity",
        "ethereum", "bitcoin", "cryptocurrency", "defi",
        "nft", "dao", "dapp", "hardhat", "truffle",
        "metamask", "ipfs", "consensus", "proof of stake",
        "hyperledger", "corda", "quorum",
    ],
}


def classify_domain(sections: Dict, full_text: str) -> Dict:
    """
    Classify the candidate's primary technical domain.
    Returns { name, confidence (0–1), breakdown { domain: pct } }.
    """
    if not full_text:
        return {"name": None, "confidence": 0.0, "breakdown": {}}

    text = full_text.lower()
    scores: Dict[str, int] = defaultdict(int)

    for domain, keywords in DOMAIN_KEYWORDS.items():
        for kw in keywords:
            if " " in kw:
                if kw in text:
                    scores[domain] += 1
            else:
                if re.search(rf"\b{re.escape(kw)}\b", text):
                    scores[domain] += 1

    if not scores:
        return {"name": None, "confidence": 0.0, "breakdown": {}}

    total    = sum(scores.values())
    best     = max(scores, key=lambda d: scores[d])
    best_val = scores[best]

    breakdown = {
        d: round((v / total) * 100)
        for d, v in sorted(scores.items(), key=lambda x: x[1], reverse=True)
        if v > 0
    }

    return {
        "name":       best,
        "confidence": round(best_val / total, 2),
        "breakdown":  breakdown,
    }