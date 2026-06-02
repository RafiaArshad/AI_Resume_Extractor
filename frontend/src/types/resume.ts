// src/types/resume.ts
// ✅ EXACTLY matches backend parse_resume() output

// ─────────────────────────────
// Shared
// ─────────────────────────────

export type SkillLevel = "advanced" | "intermediate" | "beginner";

// ─────────────────────────────
// Basic Info
// ─────────────────────────────

export interface BasicInfo {
  name:     string;
  emails:   string[];
  phones:   string[];
  location: string | null;
  links:    string[];
}

// ─────────────────────────────
// Education
// ─────────────────────────────

export interface EducationEntry {
  institution: string;
  degree:      string;
  field:       string;
  duration:    string;
  start_year:  number | null;
  end_year:    number | null;
  gpa:         string | null;
  coursework:  string[];
}

// ─────────────────────────────
// Experience
// ─────────────────────────────

export interface ExperienceEntry {
  role:             string;
  company:          string;
  duration:         string;   // PRESERVES MONTHS
  start_year:       number | null;
  end_year:         number | null;
  is_current:       boolean;
  responsibilities: string[];
}

// ─────────────────────────────
// Projects
// ─────────────────────────────

export interface ProjectEntry {
  name:        string;
  description: string[];
  tech_stack:  string[];
  links:       string[];
}

// ─────────────────────────────
// Skills
// ─────────────────────────────

export interface SkillItem {
  name:       string;
  confidence: number; // 0–100
  level:      SkillLevel;
}

export interface LanguageSkills {
  high_level: SkillItem[];
  low_level:  SkillItem[];
}

export interface SkillsMap {
  technical:   SkillItem[];
  languages:   LanguageSkills;
  frameworks:  SkillItem[];
  tools:       SkillItem[];
  soft_skills: string[];
}

// ─────────────────────────────
// Certifications
// ─────────────────────────────

export interface CertEntry {
  name:          string;
  issuer:        string | null;
  date:          string | null;
  credential_id: string | null;
  url:           string | null;
}

// ─────────────────────────────
// Domain Classification
// ─────────────────────────────

export interface DomainInfo {
  name:       string | null;
  confidence: number;
  breakdown:  Record<string, number>;
}

// ─────────────────────────────
// Total Experience
// ─────────────────────────────

export interface TotalExperience {
  years:        number;
  months:       number;
  total_months: number;
  display:      string;   // e.g. "3 years 4 months"
}

export interface UIDomainBar {
  domain:     string;
  percentage: number;
}

// ─────────────────────────────
// Resume Object
// ─────────────────────────────

export interface ResumeData {
  _id?:               string;
  file_name?:         string;
  uploaded_at?:       string;
  extraction_method?: string;

  basic_info:       BasicInfo;
  summary:          string;
  education:        EducationEntry[];
  experience:       ExperienceEntry[];
  total_experience?: TotalExperience;
  projects:         ProjectEntry[];
  skills:           SkillsMap;
  certifications:   CertEntry[];
  awards:           string[];
  spoken_languages: string[];
  domain:           DomainInfo;
}

// ─────────────────────────────
// API Responses
// ─────────────────────────────

export interface UploadResponse {
  success:         boolean;
  resume_id:       string;
  education_level: string;   // ← already returned by your backend
  field:           string;   // ← already returned by your backend
  resume_number:   number;   // ← already returned by your backend
  file_name:       string;
  data:            ResumeData;  // total_experience lives inside here
  error?:          string;
}

export interface GetResumeResponse {
  success: boolean;
  resume:  ResumeData;
  error?:  string;
}

// ─────────────────────────────
// List & Delete Responses
// ─────────────────────────────

export interface ListItem {
  _id: string;
  file_name: string;
  uploaded_at: string;
}

export interface ListResponse {
  success: boolean;
  resumes: ListItem[];
  total: number;
  error?: string;
}

export interface DeleteResponse {
  success: boolean;
  message: string;
  error?: string;
}