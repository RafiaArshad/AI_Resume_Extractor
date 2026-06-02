// src/pages/ResultsPage.tsx

import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion, useScroll, useSpring, type Variants } from "framer-motion";
import {
  Mail,
  Phone,
  MapPin,
  Linkedin,
  Github,
  Globe,
  GraduationCap,
  Briefcase,
  Award,
  FolderOpen,
  Star,
  User,
  BookOpen,
  Layers,
  Cpu,
  ExternalLink,
  CalendarDays,
  BadgeCheck,
  Sparkles,
  BarChart3,
  Wand2,
  FileText,
  Clock,
  Printer,
  ArrowUpRight,
  ChevronRight,
  ShieldCheck,
  Building2,
  Trophy,
  Medal,
  Ribbon,
  Crown,
  Code2,
  Rocket,
  Menu,
  X,
} from "lucide-react";

import PageTransition from "@/components/layout/PageTransition";
import SkeletonCard from "@/components/shared/SkeletonCard";
import { getResume } from "@/services/api";
import type {
  ResumeData,
  SkillItem,
  SkillLevel,
  UIDomainBar,
} from "@/types/resume";

/* -------------------------------------------------------------------------- */
/*  Motion presets                                                            */
/* -------------------------------------------------------------------------- */

const fadeUp: Variants = {
  hidden: { opacity: 0, y: 16 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.48, ease: [0.22, 1, 0.36, 1] },
  },
};

const slideInRight: Variants = {
  hidden: { opacity: 0, x: 20 },
  show: {
    opacity: 1,
    x: 0,
    transition: { duration: 0.45, ease: [0.22, 1, 0.36, 1] },
  },
};

const stagger: Variants = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.055, delayChildren: 0.06 },
  },
};

/* -------------------------------------------------------------------------- */
/*  Tokens                                                                    */
/* -------------------------------------------------------------------------- */

const LEVEL_BADGE: Record<SkillLevel, string> = {
  advanced:
    "bg-violet-500/10 text-violet-600 dark:text-violet-300 border border-violet-400/30",
  intermediate:
    "bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-400/30",
  beginner:
    "bg-slate-500/10 text-slate-600 dark:text-slate-300 border border-slate-400/30",
};

const LEVEL_BAR: Record<SkillLevel, string> = {
  advanced: "from-violet-500 to-fuchsia-500",
  intermediate: "from-amber-400 to-orange-500",
  beginner: "from-slate-400 to-slate-500",
};

type NormalizedResume = ResumeData & {
  file_name?: string;
  uploaded_at?: string;
};

type SkillTab = "all" | "technical" | "languages" | "frameworks" | "tools";

interface CategoryConfig {
  key: SkillTab;
  label: string;
  badgeCls: string;
  barColor: string;
  icon: React.ElementType;
}

const CAT_DEFS: CategoryConfig[] = [
  {
    key: "all",
    label: "All",
    badgeCls:
      "bg-slate-500/10 text-slate-700 dark:text-slate-300 border border-slate-400/30",
    barColor: "from-slate-500 to-slate-600",
    icon: Sparkles,
  },
  {
    key: "technical",
    label: "Core",
    badgeCls:
      "bg-pink-500/10 text-pink-700 dark:text-pink-300 border border-pink-400/30",
    barColor: "from-pink-500 to-rose-500",
    icon: Wand2,
  },
  {
    key: "languages",
    label: "Languages",
    badgeCls:
      "bg-violet-500/10 text-violet-700 dark:text-violet-300 border border-violet-400/30",
    barColor: "from-violet-500 to-purple-500",
    icon: Cpu,
  },
  {
    key: "frameworks",
    label: "Frameworks",
    badgeCls:
      "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-400/30",
    barColor: "from-emerald-500 to-teal-500",
    icon: Layers,
  },
  {
    key: "tools",
    label: "Tools",
    badgeCls:
      "bg-orange-500/10 text-orange-700 dark:text-orange-300 border border-orange-400/30",
    barColor: "from-orange-400 to-amber-500",
    icon: BarChart3,
  },
];

interface CategorizedSkill extends SkillItem {
  category: Exclude<SkillTab, "all">;
  subgroup?: "high_level" | "low_level";
}

/* -------------------------------------------------------------------------- */
/*  Helpers                                                                   */
/* -------------------------------------------------------------------------- */

function humanise(input: string): string {
  return input
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .replace(/Ai Ml/i, "AI / ML")
    .replace(/Devops Cloud/i, "DevOps / Cloud")
    .replace(/Embedded/i, "Embedded / IoT");
}

function extractionLabel(method?: string): { text: string; cls: string } {
  if (!method) return { text: "", cls: "" };
  if (method.includes("llm") || method.includes("hybrid")) {
    return {
      text: "Hybrid AI + Regex",
      cls: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-400/30",
    };
  }
  return {
    text: "Regex Parser",
    cls: "bg-blue-500/10 text-blue-700 dark:text-blue-300 border-blue-400/30",
  };
}

const CERT_ICON_SET: {
  icon: React.ElementType;
  gradient: string;
  ring: string;
  iconColor: string;
}[] = [
  {
    icon: Trophy,
    gradient: "from-amber-400 to-orange-500",
    ring: "ring-amber-400/30",
    iconColor: "text-amber-600 dark:text-amber-300",
  },
  {
    icon: Medal,
    gradient: "from-violet-500 to-fuchsia-500",
    ring: "ring-violet-400/30",
    iconColor: "text-violet-600 dark:text-violet-300",
  },
  {
    icon: ShieldCheck,
    gradient: "from-emerald-500 to-teal-500",
    ring: "ring-emerald-400/30",
    iconColor: "text-emerald-600 dark:text-emerald-300",
  },
  {
    icon: Award,
    gradient: "from-blue-500 to-cyan-500",
    ring: "ring-blue-400/30",
    iconColor: "text-blue-600 dark:text-blue-300",
  },
  {
    icon: Crown,
    gradient: "from-pink-500 to-rose-500",
    ring: "ring-pink-400/30",
    iconColor: "text-pink-600 dark:text-pink-300",
  },
  {
    icon: Ribbon,
    gradient: "from-indigo-500 to-violet-500",
    ring: "ring-indigo-400/30",
    iconColor: "text-indigo-600 dark:text-indigo-300",
  },
  {
    icon: BadgeCheck,
    gradient: "from-fuchsia-500 to-pink-500",
    ring: "ring-fuchsia-400/30",
    iconColor: "text-fuchsia-600 dark:text-fuchsia-300",
  },
  {
    icon: Sparkles,
    gradient: "from-purple-500 to-indigo-500",
    ring: "ring-purple-400/30",
    iconColor: "text-purple-600 dark:text-purple-300",
  },
];

function getCertVisual(name: string, index: number) {
  const lower = (name || "").toLowerCase();
  if (lower.includes("aws") || lower.includes("amazon")) return CERT_ICON_SET[3];
  if (lower.includes("google") || lower.includes("gcp")) return CERT_ICON_SET[2];
  if (lower.includes("microsoft") || lower.includes("azure")) return CERT_ICON_SET[1];
  if (lower.includes("ai") || lower.includes("ml") || lower.includes("data"))
    return CERT_ICON_SET[7];
  if (lower.includes("security") || lower.includes("cyber")) return CERT_ICON_SET[2];
  if (lower.includes("project") || lower.includes("pm") || lower.includes("scrum"))
    return CERT_ICON_SET[4];
  return CERT_ICON_SET[index % CERT_ICON_SET.length];
}

function buildDomainBars(data: ResumeData): UIDomainBar[] {
  return Object.entries(data.domain?.breakdown ?? {})
    .map(([domain, percentage]) => ({ domain, percentage }))
    .sort((a, b) => b.percentage - a.percentage);
}

function normalizeResume(
  raw: Record<string, unknown> | ResumeData | { data: ResumeData },
): NormalizedResume {
  const hasResumeData = (obj: unknown): obj is ResumeData =>
    !!(
      obj &&
      typeof obj === "object" &&
      ("basic_info" in obj || "summary" in obj || "skills" in obj)
    );

  const base: ResumeData = hasResumeData(raw)
    ? raw
    : hasResumeData((raw as Record<string, unknown>).data)
      ? ((raw as Record<string, unknown>).data as ResumeData)
      : ({
          basic_info: {
            name: "",
            emails: [],
            phones: [],
            location: null,
            links: [],
          },
          summary: "",
          education: [],
          experience: [],
          projects: [],
          skills: {
            technical: [],
            languages: { high_level: [], low_level: [] },
            frameworks: [],
            tools: [],
            soft_skills: [],
          },
          certifications: [],
          awards: [],
          spoken_languages: [],
          domain: { name: null, confidence: 0, breakdown: {} },
          extraction_method: "",
        } as ResumeData);

  const rawRecord = raw as Record<string, unknown>;
  return {
    ...base,
    file_name: (base._id ? (rawRecord?.file_name as string) : undefined) ?? "",
  };
}

function flattenSkills(data: ResumeData): CategorizedSkill[] {
  const out: CategorizedSkill[] = [];
  (data.skills?.technical ?? []).forEach((s) =>
    out.push({ ...s, category: "technical" }),
  );
  (data.skills?.languages?.high_level ?? []).forEach((s) =>
    out.push({ ...s, category: "languages", subgroup: "high_level" }),
  );
  (data.skills?.languages?.low_level ?? []).forEach((s) =>
    out.push({ ...s, category: "languages", subgroup: "low_level" }),
  );
  (data.skills?.frameworks ?? []).forEach((s) =>
    out.push({ ...s, category: "frameworks" }),
  );
  (data.skills?.tools ?? []).forEach((s) => out.push({ ...s, category: "tools" }));
  return out.sort((a, b) => b.confidence - a.confidence);
}

function getCategoryItems(
  data: ResumeData,
  tab: Exclude<SkillTab, "all">,
): CategorizedSkill[] {
  switch (tab) {
    case "technical":
      return (data.skills?.technical ?? []).map((s) => ({
        ...s,
        category: "technical" as const,
      }));
    case "languages":
      return [
        ...(data.skills?.languages?.high_level ?? []).map((s) => ({
          ...s,
          category: "languages" as const,
          subgroup: "high_level" as const,
        })),
        ...(data.skills?.languages?.low_level ?? []).map((s) => ({
          ...s,
          category: "languages" as const,
          subgroup: "low_level" as const,
        })),
      ];
    case "frameworks":
      return (data.skills?.frameworks ?? []).map((s) => ({
        ...s,
        category: "frameworks" as const,
      }));
    case "tools":
      return (data.skills?.tools ?? []).map((s) => ({
        ...s,
        category: "tools" as const,
      }));
    default:
      return [];
  }
}

/* -------------------------------------------------------------------------- */
/*  Reusable building blocks                                                  */
/* -------------------------------------------------------------------------- */

const SectionHeader = ({
  icon: Icon,
  eyebrow,
  title,
  subtitle,
  trailing,
}: {
  icon: React.ElementType;
  eyebrow?: string;
  title: string;
  subtitle?: string;
  trailing?: React.ReactNode;
}) => (
  <div className="flex items-start justify-between gap-3 mb-5">
    <div className="flex items-start gap-3">
      <div className="w-9 h-9 rounded-xl bg-primary/10 ring-1 ring-primary/20 flex items-center justify-center shrink-0 mt-0.5">
        <Icon className="w-4 h-4 text-primary" strokeWidth={1.75} />
      </div>
      <div>
        {eyebrow && (
          <p className="text-[10px] font-semibold tracking-[0.16em] uppercase text-muted-foreground mb-0.5">
            {eyebrow}
          </p>
        )}
        <h2 className="font-semibold text-base md:text-lg tracking-tight text-foreground leading-snug">
          {title}
        </h2>
        {subtitle && (
          <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">
            {subtitle}
          </p>
        )}
      </div>
    </div>
    {trailing && <div className="shrink-0 mt-0.5">{trailing}</div>}
  </div>
);

const SectionCard = ({
  id,
  children,
  className = "",
  variants = fadeUp,
}: {
  id?: string;
  children: React.ReactNode;
  className?: string;
  variants?: Variants;
}) => (
  <motion.section
    id={id}
    variants={variants}
    initial="hidden"
    whileInView="show"
    viewport={{ once: true, margin: "-50px" }}
    className={`relative scroll-mt-24 rounded-2xl border border-border/50 bg-card/80 dark:bg-card/50 backdrop-blur-sm p-5 md:p-6 shadow-sm hover:border-primary/20 hover:shadow-md transition-all duration-300 ${className}`}
  >
    {children}
  </motion.section>
);

const InfoChip = ({
  icon: Icon,
  label,
  value,
  href,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  href?: string;
}) => (
  <motion.div
    variants={fadeUp}
    whileHover={{ y: -2, scale: 1.01 }}
    transition={{ duration: 0.2 }}
    className="group relative rounded-xl border border-border/50 bg-card/80 dark:bg-card/40 backdrop-blur p-3.5 flex items-center gap-3 hover:border-primary/30 hover:shadow-md transition-all duration-200"
  >
    <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-primary/80 to-fuchsia-500 flex items-center justify-center shrink-0 shadow-sm">
      <Icon className="w-4 h-4 text-white" strokeWidth={2} />
    </div>
    <div className="min-w-0 flex-1">
      <p className="text-[9px] text-muted-foreground uppercase tracking-[0.15em] font-semibold mb-0.5">
        {label}
      </p>
      {href ? (
        <a
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs sm:text-sm truncate text-foreground hover:text-primary block transition-colors font-medium"
        >
          {value}
        </a>
      ) : (
        <p className="text-xs sm:text-sm truncate text-foreground font-medium">
          {value}
        </p>
      )}
    </div>
    {href && (
      <ArrowUpRight className="w-3.5 h-3.5 text-muted-foreground/30 group-hover:text-primary group-hover:-translate-y-0.5 group-hover:translate-x-0.5 transition-all shrink-0" />
    )}
  </motion.div>
);

const StatPill = ({
  label,
  value,
  icon: Icon,
  gradient,
}: {
  label: string;
  value: string;
  icon: React.ElementType;
  gradient?: string;
}) => (
  <motion.div
    whileHover={{ y: -2 }}
    transition={{ duration: 0.2 }}
    className="group relative overflow-hidden rounded-xl border border-border/50 bg-card/80 dark:bg-card/40 backdrop-blur p-4 flex items-center gap-3 hover:border-primary/25 hover:shadow-md transition-all duration-200"
  >
    <div className="relative shrink-0">
      <div className="absolute inset-0 rounded-lg bg-gradient-to-br from-primary to-fuchsia-500 blur-sm opacity-20 group-hover:opacity-35 transition-opacity" />
      <div
        className={`relative w-10 h-10 rounded-lg bg-gradient-to-br ${gradient ?? "from-primary to-fuchsia-500"} flex items-center justify-center shadow-sm`}
      >
        <Icon className="w-4.5 h-4.5 text-white" strokeWidth={2} />
      </div>
    </div>
    <div>
      <p className="text-[9px] text-muted-foreground uppercase tracking-[0.15em] font-semibold mb-0.5">
        {label}
      </p>
      <p className="font-bold text-lg tabular-nums text-foreground leading-none">
        {value}
      </p>
    </div>
  </motion.div>
);

const SkillRow = ({
  skill,
  categoryLabel,
  barColor,
  showCategory,
}: {
  skill: SkillItem;
  categoryLabel?: string;
  barColor: string;
  showCategory?: boolean;
}) => (
  <motion.div
    variants={fadeUp}
    className="space-y-2 rounded-xl border border-border/50 bg-secondary/20 dark:bg-secondary/10 p-3 hover:border-primary/20 hover:bg-secondary/30 transition-all duration-200 group"
  >
    <div className="flex items-center justify-between gap-2">
      <div className="flex items-center gap-1.5 min-w-0">
        <span className="text-sm font-medium capitalize truncate text-foreground group-hover:text-primary transition-colors">
          {skill.name}
        </span>
        {showCategory && categoryLabel && (
          <span className="hidden sm:inline text-[9px] px-1.5 py-0.5 rounded-full capitalize font-semibold bg-primary/8 text-primary border border-primary/15">
            {categoryLabel}
          </span>
        )}
      </div>
      <div className="flex items-center gap-1.5 shrink-0">
        <span
          className={`text-[9px] px-2 py-0.5 rounded-full capitalize font-semibold ${LEVEL_BADGE[skill.level]}`}
        >
          {skill.level}
        </span>
        <span className="text-xs font-bold text-foreground w-8 text-right tabular-nums">
          {skill.confidence}%
        </span>
      </div>
    </div>
    <div className="h-1.5 rounded-full bg-border/40 overflow-hidden">
      <motion.div
        className={`h-full rounded-full bg-gradient-to-r ${barColor}`}
        initial={{ width: 0 }}
        whileInView={{ width: `${skill.confidence}%` }}
        viewport={{ once: true }}
        transition={{ duration: 0.9, ease: "easeOut", delay: 0.05 }}
      />
    </div>
  </motion.div>
);

/* -------------------------------------------------------------------------- */
/*  Education / Experience cards                                              */
/* -------------------------------------------------------------------------- */

const EducationCard = ({ edu }: { edu: ResumeData["education"][number] }) => (
  <motion.article
    variants={fadeUp}
    whileHover={{ y: -2 }}
    transition={{ duration: 0.2 }}
    className="group relative overflow-hidden rounded-xl border border-border/50 bg-card/70 dark:bg-card/35 p-5 hover:border-primary/25 hover:shadow-md transition-all duration-200"
  >
    <div className="flex items-start gap-3.5 mb-3">
      <div className="relative shrink-0">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-fuchsia-500 flex items-center justify-center shadow-sm">
          <GraduationCap className="w-4.5 h-4.5 text-white" strokeWidth={2} />
        </div>
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-semibold text-sm text-foreground leading-snug">
          {edu.degree}
          {edu.field && (
            <span className="text-muted-foreground font-normal"> · {edu.field}</span>
          )}
        </p>
        <p className="text-xs font-medium text-primary mt-1 inline-flex items-center gap-1">
          <Building2 className="w-3 h-3" strokeWidth={2} />
          {edu.institution}
        </p>
      </div>
    </div>

    {(edu.duration || edu.gpa) && (
      <div className="flex flex-wrap gap-1.5 mb-3">
        {edu.duration && (
          <span className="text-[11px] px-2.5 py-1 rounded-full bg-secondary/50 text-muted-foreground border border-border/40 inline-flex items-center gap-1">
            <CalendarDays className="w-3 h-3" strokeWidth={1.75} />
            {edu.duration}
          </span>
        )}
        {edu.gpa && (
          <span className="text-[11px] px-2.5 py-1 rounded-full bg-primary/10 text-primary border border-primary/20 inline-flex items-center gap-1 font-semibold">
            <Star className="w-3 h-3" strokeWidth={2} fill="currentColor" />
            GPA {edu.gpa}
          </span>
        )}
      </div>
    )}

    {(edu.coursework?.length ?? 0) > 0 && (
      <div className="pt-3 border-t border-border/30">
        <p className="text-[9px] font-semibold tracking-[0.15em] uppercase text-muted-foreground mb-2">
          Coursework
        </p>
        <div className="flex flex-wrap gap-1">
          {edu.coursework.slice(0, 6).map((c) => (
            <span
              key={c}
              className="text-[11px] px-2 py-0.5 rounded-full bg-secondary/40 text-foreground/80 border border-border/40"
            >
              {c}
            </span>
          ))}
        </div>
      </div>
    )}
  </motion.article>
);

const ExperienceCard = ({ exp }: { exp: ResumeData["experience"][number] }) => (
  <motion.article
    variants={fadeUp}
    whileHover={{ y: -2 }}
    transition={{ duration: 0.2 }}
    className="group relative overflow-hidden rounded-xl border border-border/50 bg-card/70 dark:bg-card/35 p-5 hover:border-primary/25 hover:shadow-md transition-all duration-200"
  >
    <div className="flex items-start gap-3.5 mb-3">
      <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-fuchsia-500 flex items-center justify-center shadow-sm shrink-0">
        <Briefcase className="w-4.5 h-4.5 text-white" strokeWidth={2} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <p className="font-semibold text-sm text-foreground leading-snug">{exp.role}</p>
          {exp.is_current && (
            <span className="text-[9px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-300 border border-emerald-400/30 shrink-0 inline-flex items-center gap-1 font-semibold">
              <span className="w-1 h-1 rounded-full bg-emerald-500 animate-pulse" />
              Current
            </span>
          )}
        </div>
        <p className="text-xs font-medium text-primary mt-1 inline-flex items-center gap-1">
          <Building2 className="w-3 h-3" strokeWidth={2} />
          {exp.company}
        </p>
      </div>
    </div>

    {exp.duration && (
      <div className="mb-3">
        <span className="text-[11px] px-2.5 py-1 rounded-full bg-secondary/50 text-muted-foreground border border-border/40 inline-flex items-center gap-1">
          <CalendarDays className="w-3 h-3" strokeWidth={1.75} />
          {exp.duration}
        </span>
      </div>
    )}

    {(exp.responsibilities?.length ?? 0) > 0 && (
      <div className="pt-3 border-t border-border/30">
        <p className="text-[9px] font-semibold tracking-[0.15em] uppercase text-muted-foreground mb-2">
          Responsibilities
        </p>
        <ul className="space-y-1.5">
          {exp.responsibilities.slice(0, 4).map((r, j) => (
            <li key={j} className="text-xs text-muted-foreground flex gap-2 leading-relaxed">
              <span className="mt-[7px] w-1 h-1 rounded-full bg-primary shrink-0" />
              <span>{r}</span>
            </li>
          ))}
        </ul>
      </div>
    )}
  </motion.article>
);

/* -------------------------------------------------------------------------- */
/*  Skills section                                                            */
/* -------------------------------------------------------------------------- */

const SkillsSection = ({ data }: { data: ResumeData }) => {
  const [activeTab, setActiveTab] = useState<SkillTab>("all");

  const populatedTabs = CAT_DEFS.filter((d) => {
    if (d.key === "all") return true;
    return getCategoryItems(data, d.key).length > 0;
  });

  const totalSkills = flattenSkills(data).length;
  if (totalSkills === 0) return null;

  return (
    <SectionCard id="skills">
      <SectionHeader
        icon={Cpu}
        eyebrow="Capabilities"
        title="Skills Overview"
        subtitle="Evidence-based proficiency derived from the resume"
      />

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 mb-5">
        <StatPill
          label="Total"
          value={`${totalSkills}`}
          icon={Sparkles}
          gradient="from-primary to-fuchsia-500"
        />
        <StatPill
          label="Languages"
          value={`${
            (data.skills?.languages?.high_level?.length ?? 0) +
            (data.skills?.languages?.low_level?.length ?? 0)
          }`}
          icon={Cpu}
          gradient="from-violet-500 to-purple-500"
        />
        <StatPill
          label="Frameworks"
          value={`${data.skills?.frameworks?.length ?? 0}`}
          icon={Layers}
          gradient="from-emerald-500 to-teal-500"
        />
        <StatPill
          label="Tools"
          value={`${data.skills?.tools?.length ?? 0}`}
          icon={BarChart3}
          gradient="from-orange-400 to-amber-500"
        />
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-1.5 mb-5">
        {populatedTabs.map((tab) => {
          const count =
            tab.key === "all"
              ? totalSkills
              : getCategoryItems(data, tab.key as Exclude<SkillTab, "all">).length;
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all border inline-flex items-center gap-1.5 ${
                isActive
                  ? "bg-foreground text-background border-foreground shadow-sm"
                  : "bg-secondary/30 text-secondary-foreground border-border/50 hover:border-primary/35 hover:text-foreground"
              }`}
            >
              {tab.label}
              <span
                className={`text-[9px] px-1.5 py-0.5 rounded-full tabular-nums font-bold ${
                  isActive
                    ? "bg-background/15 text-background"
                    : "bg-foreground/5 text-muted-foreground"
                }`}
              >
                {count}
              </span>
            </button>
          );
        })}
      </div>

      <motion.div
        key={activeTab}
        variants={stagger}
        initial="hidden"
        animate="show"
        className="space-y-4"
      >
        {activeTab === "all" && (
          <div className="grid sm:grid-cols-2 gap-2">
            {flattenSkills(data).map((skill) => {
              const catDef = CAT_DEFS.find((d) => d.key === skill.category);
              const barColor = catDef?.barColor ?? LEVEL_BAR[skill.level];
              return (
                <SkillRow
                  key={`${skill.category}-${skill.subgroup ?? "main"}-${skill.name}`}
                  skill={skill}
                  categoryLabel={catDef?.label}
                  barColor={barColor}
                  showCategory
                />
              );
            })}
          </div>
        )}

        {activeTab === "languages" && (
          <div className="grid sm:grid-cols-2 gap-4">
            <div className="rounded-xl border border-border/50 bg-secondary/15 p-4 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-sm text-foreground">High Level</h3>
                <span className="text-xs text-muted-foreground tabular-nums">
                  {data.skills?.languages?.high_level?.length ?? 0}
                </span>
              </div>
              <div className="space-y-2">
                {(data.skills?.languages?.high_level ?? []).map((skill) => (
                  <SkillRow
                    key={`high-${skill.name}`}
                    skill={skill}
                    barColor="from-violet-500 to-purple-500"
                  />
                ))}
              </div>
            </div>
            <div className="rounded-xl border border-border/50 bg-secondary/15 p-4 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-sm text-foreground">Low Level</h3>
                <span className="text-xs text-muted-foreground tabular-nums">
                  {data.skills?.languages?.low_level?.length ?? 0}
                </span>
              </div>
              <div className="space-y-2">
                {(data.skills?.languages?.low_level ?? []).map((skill) => (
                  <SkillRow
                    key={`low-${skill.name}`}
                    skill={skill}
                    barColor="from-slate-400 to-slate-500"
                  />
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === "technical" && (
          <div className="grid sm:grid-cols-2 gap-2">
            {(data.skills?.technical ?? []).map((skill) => (
              <SkillRow
                key={`technical-${skill.name}`}
                skill={skill}
                barColor="from-pink-500 to-rose-500"
              />
            ))}
          </div>
        )}

        {activeTab === "frameworks" && (
          <div className="grid sm:grid-cols-2 gap-2">
            {(data.skills?.frameworks ?? []).map((skill) => (
              <SkillRow
                key={`framework-${skill.name}`}
                skill={skill}
                barColor="from-emerald-500 to-teal-500"
              />
            ))}
          </div>
        )}

        {activeTab === "tools" && (
          <div className="grid sm:grid-cols-2 gap-2">
            {(data.skills?.tools ?? []).map((skill) => (
              <SkillRow
                key={`tool-${skill.name}`}
                skill={skill}
                barColor="from-orange-400 to-amber-500"
              />
            ))}
          </div>
        )}
      </motion.div>

      {(data.skills?.soft_skills?.length ?? 0) > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.1 }}
          className="mt-6 pt-5 border-t border-border/35"
        >
          <div className="flex items-center gap-2 mb-3">
            <Wand2 className="w-3.5 h-3.5 text-primary" strokeWidth={1.75} />
            <p className="text-[9px] font-semibold tracking-[0.16em] uppercase text-muted-foreground">
              Soft Skills
            </p>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {data.skills?.soft_skills?.map((s, i) => (
              <motion.span
                key={s}
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.035 }}
                whileHover={{ y: -1 }}
                className="px-2.5 py-1 rounded-full text-xs font-medium bg-primary/8 text-primary capitalize border border-primary/15 hover:border-primary/35 transition-all cursor-default"
              >
                {s}
              </motion.span>
            ))}
          </div>
        </motion.div>
      )}
    </SectionCard>
  );
};

/* -------------------------------------------------------------------------- */
/*  Mobile nav drawer                                                         */
/* -------------------------------------------------------------------------- */

const MobileNav = ({ items }: { items: NavItem[] }) => {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="lg:hidden fixed bottom-5 right-5 z-40 w-11 h-11 rounded-full bg-foreground text-background shadow-lg flex items-center justify-center print:hidden"
        aria-label="Open navigation"
      >
        <Menu className="w-4.5 h-4.5" strokeWidth={2} />
      </button>

      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-end justify-center lg:hidden print:hidden"
          onClick={() => setOpen(false)}
        >
          <motion.div
            initial={{ y: "100%" }}
            animate={{ y: 0 }}
            exit={{ y: "100%" }}
            transition={{ type: "spring", damping: 28, stiffness: 280 }}
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-md bg-card border border-border/50 rounded-t-2xl p-5 pb-8 shadow-2xl"
          >
            <div className="flex items-center justify-between mb-4">
              <p className="text-xs font-semibold tracking-[0.14em] uppercase text-muted-foreground">
                Jump to section
              </p>
              <button
                onClick={() => setOpen(false)}
                className="w-7 h-7 rounded-full bg-secondary/50 flex items-center justify-center"
              >
                <X className="w-3.5 h-3.5" strokeWidth={2} />
              </button>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {items.map((it) => (
                <a
                  key={it.id}
                  href={`#${it.id}`}
                  onClick={() => setOpen(false)}
                  className="flex items-center gap-2 p-3 rounded-xl border border-border/50 bg-secondary/20 text-sm font-medium text-foreground hover:border-primary/30 hover:text-primary transition-all"
                >
                  <it.icon className="w-3.5 h-3.5 shrink-0 text-muted-foreground" strokeWidth={1.75} />
                  {it.label}
                </a>
              ))}
            </div>
          </motion.div>
        </motion.div>
      )}
    </>
  );
};

/* -------------------------------------------------------------------------- */
/*  Section navigation (desktop)                                              */
/* -------------------------------------------------------------------------- */

interface NavItem {
  id: string;
  label: string;
  icon: React.ElementType;
}

const SectionNav = ({ items }: { items: NavItem[] }) => {
  const [active, setActive] = useState<string>(items[0]?.id ?? "");

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio);
        if (visible[0]) setActive(visible[0].target.id);
      },
      { rootMargin: "-25% 0px -55% 0px", threshold: [0, 0.25, 0.5, 0.75, 1] },
    );
    items.forEach((it) => {
      const el = document.getElementById(it.id);
      if (el) observer.observe(el);
    });
    return () => observer.disconnect();
  }, [items]);

  return (
    <nav
      aria-label="Resume sections"
      className="hidden lg:block sticky top-24 self-start min-w-[140px]"
    >
      <p className="text-[9px] font-semibold tracking-[0.16em] uppercase text-muted-foreground mb-2.5 pl-2">
        Contents
      </p>
      <ul className="space-y-0.5">
        {items.map((it) => {
          const isActive = active === it.id;
          return (
            <li key={it.id}>
              <a
                href={`#${it.id}`}
                className={`group flex items-center gap-2 pl-2 pr-1 py-1.5 rounded-lg text-xs transition-all border-l-2 ${
                  isActive
                    ? "border-primary text-foreground bg-primary/6 font-semibold"
                    : "border-transparent text-muted-foreground hover:text-foreground hover:bg-secondary/30"
                }`}
              >
                <it.icon
                  className={`w-3 h-3 shrink-0 ${isActive ? "text-primary" : ""}`}
                  strokeWidth={1.75}
                />
                <span className="truncate">{it.label}</span>
                <ChevronRight
                  className={`w-3 h-3 ml-auto shrink-0 transition-all ${
                    isActive
                      ? "text-primary opacity-100"
                      : "opacity-0 group-hover:opacity-40"
                  }`}
                />
              </a>
            </li>
          );
        })}
      </ul>
    </nav>
  );
};

/* -------------------------------------------------------------------------- */
/*  Page                                                                      */
/* -------------------------------------------------------------------------- */

const ResultsPage = () => {
  const { resumeId } = useParams<{ resumeId: string }>();
  const navigate = useNavigate();

  const [data, setData] = useState<NormalizedResume | null>(null);
  const [domainBars, setDomainBars] = useState<UIDomainBar[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: containerRef });
  const progressX = useSpring(scrollYProgress, {
    stiffness: 120,
    damping: 24,
    mass: 0.3,
  });

  useEffect(() => {
    if (!resumeId) {
      setError("No resume ID provided.");
      setLoading(false);
      return;
    }
    (async () => {
      try {
        const resp = await getResume(resumeId);
        const raw = (
          (resp as unknown as Record<string, unknown>)?.resume ??
          (resp as unknown as Record<string, unknown>)?.data ??
          (resp as unknown as Record<string, unknown>)
        ) as Record<string, unknown>;
        const normalized = normalizeResume(raw);
        setData(normalized);
        setDomainBars(buildDomainBars(normalized));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load resume.");
      } finally {
        setLoading(false);
      }
    })();
  }, [resumeId]);

  const info = data?.basic_info;
  const badge = extractionLabel(data?.extraction_method);

  const linkIcon = (url: string) => {
    const u = url.toLowerCase();
    if (u.includes("linkedin")) return Linkedin;
    if (u.includes("github")) return Github;
    return Globe;
  };

  const navItems: NavItem[] = useMemo(() => {
    if (!data) return [];
    const list: NavItem[] = [{ id: "overview", label: "Overview", icon: User }];
    if (data.summary) list.push({ id: "summary", label: "Summary", icon: BookOpen });
    if ((data.education?.length ?? 0) > 0)
      list.push({ id: "education", label: "Education", icon: GraduationCap });
    if ((data.experience?.length ?? 0) > 0)
      list.push({ id: "experience", label: "Experience", icon: Briefcase });
    if (flattenSkills(data).length > 0)
      list.push({ id: "skills", label: "Skills", icon: Cpu });
    if (domainBars.length > 0)
      list.push({ id: "domain", label: "Domain", icon: Layers });
    if ((data.projects?.length ?? 0) > 0)
      list.push({ id: "projects", label: "Projects", icon: FolderOpen });
    if ((data.certifications?.length ?? 0) > 0)
      list.push({ id: "certifications", label: "Certs", icon: BadgeCheck });
    if ((data.spoken_languages?.length ?? 0) > 0)
      list.push({ id: "spoken", label: "Languages", icon: Globe });
    if ((data.awards?.length ?? 0) > 0)
      list.push({ id: "awards", label: "Awards", icon: Star });
    return list;
  }, [data, domainBars.length]);

  /* ----------------------- Loading / Error -------------------------------- */

  if (loading) {
    return (
      <PageTransition>
        <div className="min-h-screen pt-20 pb-16">
          <div className="container mx-auto px-4 max-w-5xl">
            <SkeletonCard />
          </div>
        </div>
      </PageTransition>
    );
  }

  if (error || !data || !info) {
    return (
      <PageTransition>
        <div className="min-h-screen pt-20 pb-16 flex flex-col items-center justify-center gap-4 px-5 text-center">
          <div className="w-12 h-12 rounded-2xl bg-destructive/10 ring-1 ring-destructive/20 flex items-center justify-center">
            <FileText className="w-5 h-5 text-destructive" strokeWidth={1.75} />
          </div>
          <div>
            <p className="text-foreground font-semibold text-base">
              {error || "No resume data found."}
            </p>
            <p className="text-sm text-muted-foreground mt-1">
              We couldn't load this extraction. Please try again.
            </p>
          </div>
          <button
            onClick={() => navigate("/upload")}
            className="px-5 py-2.5 rounded-xl bg-foreground text-background text-sm font-semibold hover:opacity-90 transition-opacity inline-flex items-center gap-2"
          >
            Upload another resume
            <ArrowUpRight className="w-4 h-4" />
          </button>
        </div>
      </PageTransition>
    );
  }

  /* ------------------------------- Render --------------------------------- */

  return (
    <PageTransition>
      {/* Progress bar */}
      <motion.div
        style={{ scaleX: progressX }}
        className="fixed top-0 left-0 right-0 h-[2px] origin-left z-50 bg-gradient-to-r from-primary via-fuchsia-500 to-violet-500 print:hidden"
      />

      {/* Background blobs */}
      <div
        aria-hidden
        className="pointer-events-none fixed inset-0 -z-10 overflow-hidden print:hidden"
      >
        <div className="absolute -top-32 -left-32 w-[360px] h-[360px] rounded-full bg-primary/8 blur-3xl" />
        <div className="absolute top-1/3 -right-32 w-[400px] h-[400px] rounded-full bg-fuchsia-500/6 blur-3xl" />
        <div className="absolute bottom-0 left-1/4 w-[300px] h-[300px] rounded-full bg-violet-500/5 blur-3xl" />
      </div>

      {/* Mobile nav */}
      <MobileNav items={navItems} />

      <div ref={containerRef} className="min-h-screen pt-20 pb-20">
        <div className="container mx-auto px-4 sm:px-5 max-w-5xl">
          <div className="grid lg:grid-cols-[148px_minmax(0,1fr)] gap-6 xl:gap-8">
            <SectionNav items={navItems} />

            <div className="space-y-4 min-w-0">
              {/* ── Hero / Overview ── */}
              <motion.section
                id="overview"
                initial={{ opacity: 0, y: 18 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
                className="relative overflow-hidden rounded-2xl border border-border/50 bg-card/80 dark:bg-card/50 backdrop-blur-sm p-5 md:p-6 shadow-sm scroll-mt-24"
              >
                {/* Dot grid texture */}
                <div
                  aria-hidden
                  className="absolute inset-0 opacity-[0.03] dark:opacity-[0.05] [background-image:radial-gradient(circle_at_1px_1px,currentColor_1px,transparent_0)] [background-size:20px_20px]"
                />
                {/* Gradient accent */}
                <div
                  aria-hidden
                  className="absolute top-0 right-0 w-48 h-48 rounded-full bg-gradient-to-bl from-primary/10 to-fuchsia-500/5 blur-2xl"
                />

                <div className="relative">
                  <div className="flex items-start gap-4 mb-4">
                    <motion.div
                      initial={{ scale: 0.8, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      transition={{ duration: 0.4, delay: 0.1 }}
                      className="relative shrink-0"
                    >
                      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-primary to-fuchsia-500 blur-lg opacity-30" />
                      <div className="relative w-12 h-12 md:w-14 md:h-14 rounded-2xl bg-gradient-to-br from-primary to-fuchsia-500 flex items-center justify-center shadow-md ring-1 ring-white/10">
                        <User className="w-6 h-6 text-white" strokeWidth={2} />
                      </div>
                    </motion.div>

                    <div className="flex-1 min-w-0">
                      <motion.p
                        initial={{ opacity: 0, y: 5 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.35, delay: 0.12 }}
                        className="text-[10px] font-semibold tracking-[0.16em] uppercase text-muted-foreground mb-1"
                      >
                        Extraction Results
                      </motion.p>
                      <motion.h1
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.4, delay: 0.15 }}
                        className="text-2xl sm:text-3xl md:text-4xl font-bold leading-tight tracking-tight text-foreground"
                      >
                        {info.name || "Unknown Candidate"}
                      </motion.h1>
                      <motion.p
                        initial={{ opacity: 0, y: 5 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.35, delay: 0.2 }}
                        className="text-xs sm:text-sm text-muted-foreground mt-1"
                      >
                        AI-parsed resume · ready for review
                      </motion.p>
                    </div>
                  </div>

                  {/* Meta badges */}
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.35, delay: 0.28 }}
                    className="flex flex-wrap items-center gap-1.5"
                  >
                    {data.file_name && (
                      <span className="px-2.5 py-1 rounded-full text-[11px] font-medium bg-secondary/40 backdrop-blur border border-border/50 inline-flex items-center gap-1 text-foreground">
                        <FileText className="w-2.5 h-2.5" strokeWidth={1.75} />
                        {data.file_name}
                      </span>
                    )}
                    {badge.text && (
                      <span
                        className={`px-2.5 py-1 rounded-full text-[11px] font-semibold border inline-flex items-center gap-1 ${badge.cls}`}
                      >
                        <ShieldCheck className="w-2.5 h-2.5" strokeWidth={1.75} />
                        {badge.text}
                      </span>
                    )}
                    {data.uploaded_at && (
                      <span className="px-2.5 py-1 rounded-full text-[11px] font-medium bg-secondary/40 backdrop-blur border border-border/50 inline-flex items-center gap-1 text-foreground">
                        <Clock className="w-2.5 h-2.5" strokeWidth={1.75} />
                        {data.uploaded_at}
                      </span>
                    )}
                  </motion.div>
                </div>
              </motion.section>

              {/* ── Contact chips ── */}
              <motion.div
                variants={stagger}
                initial="hidden"
                animate="show"
                className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5"
              >
                {info.name && (
                  <InfoChip icon={User} label="Name" value={info.name} />
                )}
                {info.emails?.[0] && (
                  <InfoChip
                    icon={Mail}
                    label="Email"
                    value={info.emails[0]}
                    href={`mailto:${info.emails[0]}`}
                  />
                )}
                {info.phones?.[0] && (
                  <InfoChip
                    icon={Phone}
                    label="Phone"
                    value={info.phones[0]}
                    href={`tel:${info.phones[0].replace(/\s/g, "")}`}
                  />
                )}
                {info.location && (
                  <InfoChip icon={MapPin} label="Location" value={info.location} />
                )}
                {(info.links ?? []).slice(0, 4).map((url, i) => {
                  const Icon = linkIcon(url);
                  const href = url.startsWith("http") ? url : `https://${url}`;
                  return (
                    <InfoChip
                      key={`${url}-${i}`}
                      icon={Icon}
                      label="Link"
                      value={url}
                      href={href}
                    />
                  );
                })}
              </motion.div>

              {/* ── Summary ── */}
              {data.summary && (
                <SectionCard id="summary" variants={slideInRight}>
                  <SectionHeader
                    icon={BookOpen}
                    eyebrow="About"
                    title="Professional Summary"
                  />
                  <p className="text-sm text-muted-foreground leading-[1.8]">
                    {data.summary}
                  </p>
                </SectionCard>
              )}

              {/* ── Education + Experience ── */}
              <div className="grid lg:grid-cols-2 gap-4">
                {(data.education?.length ?? 0) > 0 && (
                  <SectionCard id="education">
                    <SectionHeader
                      icon={GraduationCap}
                      eyebrow="Background"
                      title="Education"
                    />
                    <motion.div
                      variants={stagger}
                      initial="hidden"
                      whileInView="show"
                      viewport={{ once: true }}
                      className="space-y-2.5"
                    >
                      {data.education.map((edu, i) => (
                        <EducationCard key={i} edu={edu} />
                      ))}
                    </motion.div>
                  </SectionCard>
                )}

                {/* ── Experience ── */}
                {(data.experience?.length ?? 0) > 0 && (
                  <SectionCard id="experience">
                    <SectionHeader
                      icon={Briefcase}
                      eyebrow="Career"
                      title="Experience"
                      trailing={
                        data.total_experience?.display ? (
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-primary/10 text-primary border border-primary/20">
                            <Clock className="w-3 h-3" strokeWidth={1.75} />
                            {data.total_experience.display}
                          </span>
                        ) : undefined
                      }
                    />
                    <motion.div
                      variants={stagger}
                      initial="hidden"
                      whileInView="show"
                      viewport={{ once: true }}
                      className="space-y-2.5"
                    >
                      {data.experience.map((exp, i) => (
                        <ExperienceCard key={i} exp={exp} />
                      ))}
                    </motion.div>
                  </SectionCard>
                )}
              </div>

              {/* ── Skills ── */}
              <SkillsSection data={data} />

              {/* ── Domain ── */}
              {domainBars.length > 0 && (
                <SectionCard id="domain">
                  <SectionHeader
                    icon={Layers}
                    eyebrow="Specialization"
                    title="Domain Classification"
                    trailing={
                      data.domain?.name ? (
                        <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-foreground text-background">
                          {humanise(data.domain.name)}
                        </span>
                      ) : null
                    }
                  />
                  <div className="space-y-3.5">
                    {domainBars.map((bar, idx) => (
                      <div key={bar.domain} className="space-y-1.5">
                        <div className="flex justify-between text-xs">
                          <span className="font-medium text-foreground">
                            {humanise(bar.domain)}
                          </span>
                          <span className="text-muted-foreground tabular-nums font-semibold">
                            {bar.percentage}%
                          </span>
                        </div>
                        <div className="h-2 rounded-full bg-border/40 overflow-hidden">
                          <motion.div
                            className={`h-full rounded-full bg-gradient-to-r ${
                              idx === 0
                                ? "from-primary to-fuchsia-500"
                                : idx === 1
                                  ? "from-violet-500 to-purple-500"
                                  : "from-slate-400 to-slate-500"
                            }`}
                            initial={{ width: 0 }}
                            whileInView={{ width: `${bar.percentage}%` }}
                            viewport={{ once: true }}
                            transition={{
                              duration: 0.9,
                              ease: "easeOut",
                              delay: idx * 0.05,
                            }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </SectionCard>
              )}

              {/* ── Projects ── */}
              {(data.projects?.length ?? 0) > 0 && (
                <SectionCard id="projects">
                  <SectionHeader
                    icon={FolderOpen}
                    eyebrow="Selected Work"
                    title="Projects"
                    trailing={
                      <span className="text-xs text-muted-foreground tabular-nums">
                        {data.projects.length} project
                        {data.projects.length !== 1 ? "s" : ""}
                      </span>
                    }
                  />
                  <div className="grid sm:grid-cols-2 gap-4">
                    {data.projects.map((proj, i) => {
                      const ProjIcon =
                        i % 3 === 0 ? Rocket : i % 3 === 1 ? Code2 : FolderOpen;
                      return (
                        <motion.article
                          key={i}
                          whileHover={{ y: -3 }}
                          transition={{ duration: 0.2 }}
                          className="group relative overflow-hidden rounded-xl border border-border/50 bg-card/70 dark:bg-card/35 hover:border-primary/25 hover:shadow-lg hover:shadow-primary/5 transition-all duration-200"
                        >
                          <span
                            aria-hidden
                            className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-primary via-fuchsia-500 to-violet-500 opacity-60 group-hover:opacity-100 transition-opacity"
                          />
                          <div className="relative p-5 space-y-3">
                            <div className="flex items-start gap-3">
                              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-fuchsia-500 flex items-center justify-center shadow-sm shrink-0">
                                <ProjIcon
                                  className="w-4.5 h-4.5 text-white"
                                  strokeWidth={2}
                                />
                              </div>
                              <div className="flex-1 min-w-0 pt-0.5">
                                <h3 className="font-semibold text-sm leading-snug text-foreground group-hover:text-primary transition-colors">
                                  {proj.name || "Untitled Project"}
                                </h3>
                                <p className="text-[9px] font-semibold tracking-[0.14em] uppercase text-muted-foreground mt-0.5">
                                  Project
                                </p>
                              </div>
                              {(proj.links?.length ?? 0) > 0 && (
                                <a
                                  href={proj.links[0]}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="shrink-0 w-8 h-8 rounded-lg bg-secondary/40 border border-border/50 hover:bg-gradient-to-br hover:from-primary hover:to-fuchsia-500 hover:text-white hover:border-transparent flex items-center justify-center transition-all"
                                  aria-label="Open project"
                                >
                                  <ExternalLink className="w-3.5 h-3.5" strokeWidth={2} />
                                </a>
                              )}
                            </div>

                            {(proj.description?.length ?? 0) > 0 && (
                              <p className="text-xs text-muted-foreground leading-relaxed">
                                {proj.description.join(" ")}
                              </p>
                            )}

                            {(proj.tech_stack?.length ?? 0) > 0 && (
                              <div className="pt-2.5 border-t border-border/30">
                                <div className="flex flex-wrap gap-1">
                                  {proj.tech_stack.map((t) => (
                                    <span
                                      key={t}
                                      className="px-2 py-0.5 text-[10px] rounded-full bg-primary/8 text-primary capitalize border border-primary/15 font-medium"
                                    >
                                      {t}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        </motion.article>
                      );
                    })}
                  </div>
                </SectionCard>
              )}

              {/* ── Certifications ── */}
              {(data.certifications?.length ?? 0) > 0 && (
                <SectionCard id="certifications">
                  <SectionHeader
                    icon={BadgeCheck}
                    eyebrow="Credentials"
                    title="Certifications"
                    trailing={
                      <span className="text-xs text-muted-foreground tabular-nums">
                        {data.certifications.length}
                      </span>
                    }
                  />
                  <div className="grid sm:grid-cols-2 gap-4">
                    {data.certifications.map((cert, i) => {
                      const visual = getCertVisual(cert.name, i);
                      const CertIcon = visual.icon;
                      return (
                        <motion.article
                          key={i}
                          whileHover={{ y: -2 }}
                          transition={{ duration: 0.2 }}
                          className="group relative overflow-hidden rounded-xl border border-border/50 bg-card/70 dark:bg-card/35 hover:border-primary/25 hover:shadow-md transition-all duration-200"
                        >
                          <span
                            aria-hidden
                            className={`absolute -top-12 -right-12 w-32 h-32 rounded-full bg-gradient-to-br ${visual.gradient} opacity-[0.07] blur-2xl group-hover:opacity-15 transition-opacity duration-400`}
                          />
                          <div className="relative p-5 space-y-3">
                            <div className="flex items-start gap-3">
                              <div
                                className={`w-10 h-10 rounded-xl bg-gradient-to-br ${visual.gradient} flex items-center justify-center shadow-sm shrink-0`}
                              >
                                <CertIcon className="w-4.5 h-4.5 text-white" strokeWidth={2} />
                              </div>
                              <div className="flex-1 min-w-0 pt-0.5">
                                <p className="text-sm font-medium leading-snug text-foreground group-hover:text-primary transition-colors">
                                  {cert.name}
                                </p>
                                {cert.issuer && (
                                  <p className="text-xs text-primary mt-1 inline-flex items-center gap-1">
                                    <Building2 className="w-3 h-3" strokeWidth={2} />
                                    {cert.issuer}
                                  </p>
                                )}
                              </div>
                            </div>

                            {(cert.date || cert.credential_id) && (
                              <div className="flex flex-wrap gap-1.5">
                                {cert.date && (
                                  <span className="text-[11px] px-2 py-0.5 rounded-full bg-secondary/40 text-muted-foreground border border-border/40 inline-flex items-center gap-1">
                                    <CalendarDays className="w-2.5 h-2.5" strokeWidth={1.75} />
                                    {cert.date}
                                  </span>
                                )}
                                {cert.credential_id && (
                                  <span className="text-[11px] px-2 py-0.5 rounded-full bg-secondary/40 text-muted-foreground border border-border/40 inline-flex items-center gap-1">
                                    ID{" "}
                                    <span className="font-mono text-foreground/75">
                                      {cert.credential_id}
                                    </span>
                                  </span>
                                )}
                              </div>
                            )}

                            {cert.url && (
                              <div className="pt-2.5 border-t border-border/30">
                                <a
                                  href={cert.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-xs text-primary inline-flex items-center gap-1 hover:gap-1.5 transition-all font-semibold"
                                >
                                  Verify credential
                                  <ArrowUpRight className="w-3 h-3" strokeWidth={2} />
                                </a>
                              </div>
                            )}
                          </div>
                        </motion.article>
                      );
                    })}
                  </div>
                </SectionCard>
              )}

              {/* ── Spoken Languages ── */}
              {(data.spoken_languages?.length ?? 0) > 0 && (
                <SectionCard id="spoken">
                  <SectionHeader
                    icon={Globe}
                    eyebrow="Communication"
                    title="Spoken Languages"
                  />
                  <div className="flex flex-wrap gap-1.5">
                    {data.spoken_languages.map((lang) => (
                      <span
                        key={lang}
                        className="px-3 py-1.5 rounded-full text-xs font-medium bg-secondary/50 text-foreground border border-border/40 hover:border-primary/25 transition-colors"
                      >
                        {lang}
                      </span>
                    ))}
                  </div>
                </SectionCard>
              )}

              {/* ── Awards ── */}
              {(data.awards?.length ?? 0) > 0 && (
                <SectionCard id="awards">
                  <SectionHeader
                    icon={Award}
                    eyebrow="Recognition"
                    title="Awards & Achievements"
                  />
                  <div className="space-y-2">
                    {data.awards.map((award, i) => (
                      <div
                        key={i}
                        className="flex items-start gap-3 p-3 rounded-xl bg-secondary/20 border border-border/40 hover:border-primary/20 transition-colors"
                      >
                        <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-amber-400/20 to-orange-500/20 ring-1 ring-amber-400/25 flex items-center justify-center shrink-0 mt-0.5">
                          <Star className="w-3.5 h-3.5 text-amber-500" strokeWidth={1.75} />
                        </div>
                        <span className="text-sm text-foreground leading-relaxed">
                          {award}
                        </span>
                      </div>
                    ))}
                  </div>
                </SectionCard>
              )}

              {/* ── Footer actions ── */}
              <motion.div
                variants={fadeUp}
                initial="hidden"
                whileInView="show"
                viewport={{ once: true }}
                className="flex flex-col sm:flex-row gap-2.5 justify-center pt-6 border-t border-border/35 print:hidden"
              >
                <motion.button
                  whileHover={{ y: -2 }}
                  whileTap={{ scale: 0.97 }}
                  onClick={() => navigate("/upload")}
                  className="flex-1 sm:flex-none px-5 py-2.5 rounded-xl bg-foreground text-background text-sm font-semibold inline-flex items-center justify-center gap-2 shadow-md hover:opacity-90 transition-opacity"
                >
                  <Sparkles className="w-4 h-4" strokeWidth={1.75} />
                  Parse Another Resume
                </motion.button>
                <motion.button
                  whileHover={{ y: -2 }}
                  whileTap={{ scale: 0.97 }}
                  onClick={() => window.print()}
                  className="flex-1 sm:flex-none px-5 py-2.5 rounded-xl border border-border bg-card/70 text-sm font-semibold text-foreground inline-flex items-center justify-center gap-2 hover:border-primary/35 hover:text-primary transition-colors"
                >
                  <Printer className="w-4 h-4" strokeWidth={1.75} />
                  Print / Save PDF
                </motion.button>
              </motion.div>

              <p className="text-center text-[11px] text-muted-foreground mt-3 print:hidden pb-2">
                Generated by AI-assisted resume extraction · reviewed for accuracy
              </p>
            </div>
          </div>
        </div>
      </div>
    </PageTransition>
  );
};

export default ResultsPage;