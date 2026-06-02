// src/pages/SearchPage.tsx

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  ChevronRight,
  FileText,
  Layers,
  X,
  ArrowUpRight,
  Clock,
  CalendarDays,
  AlertCircle,
  ChevronDown,
} from "lucide-react";

import PageTransition from "@/components/layout/PageTransition";
import { listResumes, searchResumes } from "@/services/api";

/* ------------------------------------------------------------------ */
/* TYPES                                                              */
/* ------------------------------------------------------------------ */

interface ApiResumeItem {
  _id?: string;
  id?: number;
  resume_number?: number;
  file_name?: string;
  uploaded_at?: string;
  candidate_name?: string | null;
  extraction_method?: string;
  status?: string;
  field?: string;
  education_level?: string;
  domain?: {
    name?: string | null;
    confidence?: number;
    breakdown?: Record<string, number>;
  } | null;
}

interface ResumeListItem {
  mongo_id?: string;
  id: number;
  resume_number: number;
  file_name: string;
  uploaded_at: string;
  candidate_name: string | null;
  extraction_method: string;
  status: string;
  field: string;
  education_level: string;
  domain: {
    name: string | null;
    confidence: number;
    breakdown: Record<string, number>;
  } | null;
}

/* ------------------------------------------------------------------ */
/* MULTI-TERM PARSER                                                  */
/*                                                                    */
/* "C++, Python"     → ["C++", "Python"]                             */
/* "C++ Python"      → ["C++", "Python"]                             */
/* "React and Node"  → ["React", "Node"]                             */
/* "React; Node"     → ["React", "Node"]                             */
/* Single term kept intact, tokens < 2 chars dropped.                */
/* ------------------------------------------------------------------ */

function parseSearchTerms(raw: string): string[] {
  if (!raw.trim()) return [];
  return raw
    .split(/,|;|\band\b/i)
    .flatMap((chunk) => {
      const t = chunk.trim();
      return t.includes(" ") ? t.split(/\s+/) : [t];
    })
    .map((t) => t.trim())
    .filter((t) => t.length >= 2)
    .filter(
      (t, i, arr) =>
        arr.findIndex((x) => x.toLowerCase() === t.toLowerCase()) === i
    );
}

/* ------------------------------------------------------------------ */
/* MOTION                                                             */
/* ------------------------------------------------------------------ */

const fadeUp = {
  hidden: { opacity: 0, y: 14 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.4, ease: [0.22, 1, 0.36, 1] as const },
  },
};

const stagger = {
  hidden: {},
  show: { transition: { staggerChildren: 0.04, delayChildren: 0.05 } },
};

/* ------------------------------------------------------------------ */
/* HELPERS                                                            */
/* ------------------------------------------------------------------ */

function humanise(value: string): string {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .replace(/Ai Ml/i, "AI / ML")
    .replace(/Devops Cloud/i, "DevOps / Cloud");
}

function formatDate(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function initials(name: string | null): string {
  if (!name) return "?";
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? "")
    .join("");
}

function domainLabel(item: ResumeListItem): string {
  const d = item.domain?.name?.trim();
  if (d) return humanise(d);
  return item.field || "General";
}

const AVATAR_GRADIENTS = [
  "from-violet-500 to-fuchsia-500",
  "from-primary to-fuchsia-500",
  "from-emerald-500 to-teal-500",
  "from-amber-400 to-orange-500",
  "from-pink-500 to-rose-500",
  "from-blue-500 to-cyan-500",
  "from-indigo-500 to-violet-500",
];

function avatarGradient(name: string | null): string {
  if (!name) return AVATAR_GRADIENTS[0];
  const hash = [...name].reduce((a, c) => a + c.charCodeAt(0), 0);
  return AVATAR_GRADIENTS[hash % AVATAR_GRADIENTS.length];
}

const LEVEL_BADGE: Record<string, string> = {
  PhD:       "bg-violet-500/10 text-violet-600 dark:text-violet-300 border-violet-400/30",
  Master:    "bg-blue-500/10 text-blue-700 dark:text-blue-300 border-blue-400/30",
  Bachelor:  "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-400/30",
  Associate: "bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-400/30",
  Diploma:   "bg-pink-500/10 text-pink-700 dark:text-pink-300 border-pink-400/30",
  Other:     "bg-slate-500/10 text-slate-600 dark:text-slate-300 border-slate-400/30",
};

function levelBadgeCls(level: string): string {
  return LEVEL_BADGE[level] ?? LEVEL_BADGE.Other;
}

/* ------------------------------------------------------------------ */
/* NORMALIZER                                                         */
/* ------------------------------------------------------------------ */

function normalizeResume(item: ApiResumeItem, index: number): ResumeListItem {
  return {
    mongo_id:          item._id,
    id:                item.id ?? index + 1,
    resume_number:     item.resume_number ?? index + 1,
    file_name:         item.file_name ?? "Unknown Resume",
    uploaded_at:       item.uploaded_at ?? new Date().toISOString(),
    candidate_name:    item.candidate_name ?? "Unknown Candidate",
    extraction_method: item.extraction_method ?? "AI Extraction",
    status:            item.status ?? "processed",
    field:             item.field ?? "General",
    education_level:   item.education_level ?? "Other",
    domain: {
      name:       item.domain?.name ?? "General",
      confidence: item.domain?.confidence ?? 0,
      breakdown:  item.domain?.breakdown ?? {},
    },
  };
}

/* ------------------------------------------------------------------ */
/* RESUME CARD                                                        */
/* ------------------------------------------------------------------ */

function ResumeCard({
  item,
  onClick,
}: {
  item: ResumeListItem;
  onClick: () => void;
}) {
  return (
    <motion.article
      variants={fadeUp}
      whileHover={{ y: -3 }}
      transition={{ duration: 0.2 }}
      onClick={onClick}
      className="
        group relative overflow-hidden rounded-2xl
        border border-border/50
        bg-card/80 dark:bg-card/40 backdrop-blur-sm
        p-5 cursor-pointer
        hover:border-primary/30 hover:shadow-lg hover:shadow-primary/5
        transition-all duration-200
      "
    >
      <span
        aria-hidden
        className="
          absolute top-0 left-0 right-0 h-[2px]
          bg-gradient-to-r from-primary via-fuchsia-500 to-violet-500
          opacity-0 group-hover:opacity-100 transition-opacity duration-300
        "
      />

      <div className="flex items-start gap-4">
        <div className="relative shrink-0">
          <div
            className={`
              absolute inset-0 rounded-2xl bg-gradient-to-br
              ${avatarGradient(item.candidate_name)}
              blur-md opacity-25 group-hover:opacity-40 transition-opacity
            `}
          />
          <div
            className={`
              relative w-12 h-12 rounded-2xl bg-gradient-to-br
              ${avatarGradient(item.candidate_name)}
              flex items-center justify-center shadow-sm ring-1 ring-white/10
            `}
          >
            <span className="text-sm font-bold text-white">
              {initials(item.candidate_name)}
            </span>
          </div>
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <p className="font-semibold text-sm text-foreground group-hover:text-primary transition-colors truncate">
                {item.candidate_name}
              </p>
              <p className="text-xs text-muted-foreground mt-0.5 truncate inline-flex items-center gap-1">
                <Layers className="w-3 h-3 shrink-0" strokeWidth={1.75} />
                {domainLabel(item)}
              </p>
            </div>
            <ChevronRight className="w-4 h-4 text-muted-foreground/30 group-hover:text-primary group-hover:translate-x-0.5 transition-all shrink-0 mt-0.5" />
          </div>

          <div className="flex flex-wrap gap-1.5 mt-3">
            <span className={`text-[10px] px-2 py-0.5 rounded-full border font-semibold ${levelBadgeCls(item.education_level)}`}>
              {item.education_level}
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded-full border border-border/40 bg-secondary/40 text-muted-foreground font-medium">
              {item.field}
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded-full border border-border/40 bg-secondary/40 text-muted-foreground inline-flex items-center gap-1">
              <CalendarDays className="w-2.5 h-2.5" strokeWidth={1.75} />
              {formatDate(item.uploaded_at)}
            </span>
          </div>
        </div>
      </div>

      {item.domain?.confidence > 0 && (
        <div className="mt-4 pt-3 border-t border-border/25">
          <div className="flex justify-between text-[10px] text-muted-foreground mb-1.5">
            <span>Domain confidence</span>
            <span className="font-semibold tabular-nums">{item.domain.confidence}%</span>
          </div>
          <div className="h-1 rounded-full bg-border/30 overflow-hidden">
            <motion.div
              className="h-full rounded-full bg-gradient-to-r from-primary to-fuchsia-500"
              initial={{ width: 0 }}
              whileInView={{ width: `${item.domain.confidence}%` }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
            />
          </div>
        </div>
      )}
    </motion.article>
  );
}

/* ------------------------------------------------------------------ */
/* CONSTANTS                                                          */
/* ------------------------------------------------------------------ */

const EDUCATION_LEVELS = [
  "All",
  "Bachelor",
  "Master",
  "PhD",
  "Associate",
  "Diploma",
  "Other",
];

/* ------------------------------------------------------------------ */
/* PAGE                                                               */
/* ------------------------------------------------------------------ */

export default function SearchPage() {
  const navigate = useNavigate();

  const [allItems,  setAllItems]  = useState<ResumeListItem[]>([]);
  const [query,     setQuery]     = useState("");
  const [level,     setLevel]     = useState("All");
  const [loading,   setLoading]   = useState(true);
  const [searching, setSearching] = useState(false);
  const [error,     setError]     = useState("");
  const [total,     setTotal]     = useState(0);

  const inputRef    = useRef<HTMLInputElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  /**
   * Tracks whether the user has changed query/level at least once.
   * The debounce effect uses this to skip the very first render —
   * the dedicated mount effect (below) handles the initial data load.
   * Using a ref (not state) so flipping it never triggers a re-render.
   */
  const userHasSearched = useRef(false);

  /* ---------------------------------------------------------------- */
  /* LOAD ALL — fetches the full resume list with no filters          */
  /* ---------------------------------------------------------------- */

  const loadAll = useCallback(async () => {
  try {
    setLoading(true);
    setError("");

    const response = await searchResumes({ limit: 200 });
    const raw: ApiResumeItem[] = response?.items ?? response?.resumes ?? [];
    const normalized = raw.map((item, idx) => normalizeResume(item, idx));
    setAllItems(normalized);
    setTotal(response?.total ?? normalized.length);
  } catch (err) {
    console.error("[loadAll]", err);
    setError("Failed to load resumes. Please refresh.");
  } finally {
    setLoading(false);
  }
}, []);

  /* ---------------------------------------------------------------- */
  /* EFFECT 1 — initial mount load                                    */
  /*                                                                  */
  /* Runs once when the component mounts. Shows all resumes with      */
  /* no filters. Does NOT depend on query or level.                   */
  /* ---------------------------------------------------------------- */

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { loadAll(); }, []);

  /* ---------------------------------------------------------------- */
  /* MULTI-TERM SEARCH                                                */
  /*                                                                  */
  /* For a single term  → one API request.                           */
  /* For multiple terms → one request per term in parallel, then      */
  /*                      intersect by ID (resume must match ALL).    */
  /* ---------------------------------------------------------------- */

  const runSearch = useCallback(
    async (rawQuery: string, selectedLevel: string) => {
      const terms    = parseSearchTerms(rawQuery);
      const hasTerms = terms.length > 0;
      const hasLevel = selectedLevel !== "All";

      // All filters cleared → restore the full list
      if (!hasTerms && !hasLevel) {
        loadAll();
        return;
      }

      try {
        setSearching(true);
        setError("");

        let results: ApiResumeItem[];

        if (!hasTerms) {
          // Level-only filter
          const res = await searchResumes({ level: selectedLevel, limit: 200 });
          results = Array.isArray(res) ? res : (res?.items ?? res?.resumes ?? []);

        } else if (terms.length === 1) {
          // Single term
          const res = await searchResumes({
            keyword: terms[0],
            level:   hasLevel ? selectedLevel : undefined,
            limit:   200,
          });
          results = Array.isArray(res) ? res : (res?.items ?? res?.resumes ?? []);

        } else {
          // Multiple terms — parallel requests, then AND-intersect
          const perTerm = await Promise.all(
            terms.map((term) =>
              searchResumes({
                keyword: term,
                level:   hasLevel ? selectedLevel : undefined,
                limit:   200,
              }).then((r) =>
                (Array.isArray(r) ? r : (r?.items ?? r?.resumes ?? [])) as ApiResumeItem[]
              )
            )
          );

          // Build ID sets and intersect: keep only IDs present in every set
          const idSets = perTerm.map(
            (arr) => new Set(arr.map((item) => item._id ?? String(item.id)))
          );
          const [smallest, ...rest] = [...idSets].sort((a, b) => a.size - b.size);
          const intersected = new Set(
            [...smallest].filter((id) => rest.every((s) => s.has(id)))
          );

          // Reconstruct item objects from the first term's result array
          results = perTerm[0].filter((item) =>
            intersected.has(item._id ?? String(item.id))
          );
        }

        const normalized = results.map((item, idx) => normalizeResume(item, idx));
        setAllItems(normalized);
        setTotal(normalized.length);
      } catch (err) {
        console.error("[runSearch]", err);
        setError("Search failed. Please try again.");
      } finally {
        setSearching(false);
      }
    },
    [loadAll]
  );

  /* ---------------------------------------------------------------- */
  /* EFFECT 2 — debounced search on query / level changes             */
  /*                                                                  */
  /* Skips the very first render (Effect 1 already loaded all data).  */
  /* Every subsequent change is debounced by 400 ms.                  */
  /* ---------------------------------------------------------------- */

  useEffect(() => {
    // Skip the first time this effect fires (component just mounted).
    // Effect 1 has already kicked off loadAll(); running a second
    // fetch here would race against it and potentially wipe the results.
    if (!userHasSearched.current) {
      userHasSearched.current = true;
      return;
    }

    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      runSearch(query, level);
    }, 400);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query, level, runSearch]);

  /* ---------------------------------------------------------------- */
  /* DERIVED STATE                                                    */
  /* ---------------------------------------------------------------- */

  const activeTerms = useMemo(() => parseSearchTerms(query), [query]);

  // Safety-net level filter on the client side (harmless when backend
  // already filtered, useful when showing the unfiltered list)
  const displayed = useMemo(() => {
    if (level === "All") return allItems;
    return allItems.filter(
      (item) => item.education_level.toLowerCase() === level.toLowerCase()
    );
  }, [allItems, level]);

  const availableLevels = useMemo(() => {
    const set = new Set(
      allItems.map((item) => item.education_level).filter(Boolean)
    );
    return ["All", ...EDUCATION_LEVELS.slice(1).filter((l) => set.has(l))];
  }, [allItems]);

  const hasFilters = query.trim().length > 0 || level !== "All";

  /* ---------------------------------------------------------------- */
  /* UI                                                               */
  /* ---------------------------------------------------------------- */

  return (
    <PageTransition>
      <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute -top-32 -left-32 w-[360px] h-[360px] rounded-full bg-primary/8 blur-3xl" />
        <div className="absolute top-1/3 -right-32 w-[400px] h-[400px] rounded-full bg-fuchsia-500/6 blur-3xl" />
      </div>

      <div className="min-h-screen pt-20 pb-20">
        <div className="container mx-auto px-4 sm:px-5 max-w-5xl">

          {/* ── Header ── */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
            className="mb-8"
          >
            <p className="text-[10px] font-semibold tracking-[0.18em] uppercase text-muted-foreground mb-1.5">
              Resume Database
            </p>
            <div className="flex items-end justify-between gap-4 flex-wrap">
              <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-foreground">
                Search Resumes
              </h1>
              {!loading && (
                <span className="text-sm text-muted-foreground tabular-nums">
                  {total} resume{total !== 1 ? "s" : ""} stored
                </span>
              )}
            </div>
          </motion.div>

          {/* ── Search bar + Level dropdown ── */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.08, ease: [0.22, 1, 0.36, 1] }}
            className="flex gap-3 mb-4"
          >
            {/* Keyword input */}
            <div className="relative flex-1">
              <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
                {searching ? (
                  <Clock className="w-4 h-4 text-primary animate-spin" strokeWidth={1.75} />
                ) : (
                  <Search className="w-4 h-4 text-muted-foreground" strokeWidth={1.75} />
                )}
              </div>

              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder='Search by name, skills… e.g. "C++, Python" or "React Node.js"'
                className="
                  w-full h-12 pl-11 pr-10 rounded-2xl
                  border border-border/60
                  bg-card/80 dark:bg-card/50 backdrop-blur-sm
                  text-sm text-foreground placeholder:text-muted-foreground
                  focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/40
                  transition-all
                "
              />

              {query && (
                <button
                  onClick={() => { setQuery(""); inputRef.current?.focus(); }}
                  className="absolute inset-y-0 right-3 flex items-center px-1"
                >
                  <X className="w-3.5 h-3.5 text-muted-foreground hover:text-foreground transition-colors" />
                </button>
              )}
            </div>

            {/* Level dropdown */}
            <div className="relative shrink-0">
              <select
                value={level}
                onChange={(e) => setLevel(e.target.value)}
                className="
                  h-12 pl-4 pr-9 rounded-2xl appearance-none
                  border border-border/60
                  bg-card/80 dark:bg-card/50 backdrop-blur-sm
                  text-sm font-medium text-foreground
                  focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/40
                  cursor-pointer transition-all hover:border-primary/30
                "
              >
                {availableLevels.map((lvl) => (
                  <option key={lvl} value={lvl}>
                    {lvl === "All" ? "All Levels" : lvl}
                  </option>
                ))}
              </select>
              <span className="pointer-events-none absolute inset-y-0 right-3 flex items-center">
                <ChevronDown className="w-4 h-4 text-muted-foreground" strokeWidth={1.75} />
              </span>
            </div>
          </motion.div>

          {/* ── Active filter pills ── */}
          <AnimatePresence>
            {hasFilters && !loading && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="flex flex-wrap items-center gap-2 mb-4 overflow-hidden"
              >
                {activeTerms.map((term) => (
                  <span
                    key={term}
                    className="inline-flex items-center gap-1.5 text-xs px-3 py-1 rounded-full bg-primary/10 text-primary border border-primary/20"
                  >
                    <Search className="w-3 h-3" strokeWidth={1.75} />
                    {term}
                  </span>
                ))}

                {level !== "All" && (
                  <span className="inline-flex items-center gap-1.5 text-xs px-3 py-1 rounded-full bg-secondary/60 text-foreground border border-border/50">
                    {level}
                    <button onClick={() => setLevel("All")} className="ml-0.5 hover:opacity-70">
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                )}

                {activeTerms.length > 1 && (
                  <span className="text-[10px] text-muted-foreground">
                    matching all {activeTerms.length} terms
                  </span>
                )}

                <button
                  onClick={() => { setQuery(""); setLevel("All"); }}
                  className="ml-auto text-[10px] text-muted-foreground hover:text-foreground transition-colors"
                >
                  Clear all
                </button>
              </motion.div>
            )}
          </AnimatePresence>

          {/* ── Error ── */}
          {error && (
            <div className="flex items-center gap-3 p-4 rounded-2xl border border-destructive/30 bg-destructive/5 text-destructive text-sm mb-6">
              <AlertCircle className="w-4 h-4 shrink-0" strokeWidth={1.75} />
              {error}
            </div>
          )}

          {/* ── Skeleton ── */}
          {loading && (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <div
                  key={i}
                  className="rounded-2xl border border-border/40 bg-card/60 p-5 animate-pulse"
                >
                  <div className="flex gap-4">
                    <div className="w-12 h-12 rounded-2xl bg-secondary/60" />
                    <div className="flex-1 space-y-2 pt-1">
                      <div className="h-3.5 bg-secondary/60 rounded-full w-3/4" />
                      <div className="h-3 bg-secondary/40 rounded-full w-1/2" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* ── Empty state ── */}
          {!loading && !searching && displayed.length === 0 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex flex-col items-center justify-center py-24 text-center gap-4"
            >
              <div className="w-14 h-14 rounded-2xl bg-secondary/50 ring-1 ring-border/50 flex items-center justify-center">
                <FileText className="w-6 h-6 text-muted-foreground" strokeWidth={1.5} />
              </div>
              <div>
                <p className="font-semibold text-foreground">No matching resumes found</p>
                <p className="text-sm text-muted-foreground mt-1">
                  {activeTerms.length > 1
                    ? `No resume matched all ${activeTerms.length} terms. Try removing one.`
                    : "Try a different name, skill, or education level."}
                </p>
              </div>
              {hasFilters && (
                <button
                  onClick={() => { setQuery(""); setLevel("All"); }}
                  className="text-xs text-primary hover:underline"
                >
                  Clear all filters
                </button>
              )}
            </motion.div>
          )}

          {/* ── Results grid ── */}
          {!loading && displayed.length > 0 && (
            <>
              <AnimatePresence mode="wait">
                <motion.p
                  key={`${query}-${level}-${displayed.length}`}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="text-xs text-muted-foreground mb-3 tabular-nums"
                >
                  {searching
                    ? "Searching…"
                    : `${displayed.length} result${displayed.length !== 1 ? "s" : ""}`}
                </motion.p>
              </AnimatePresence>

              <motion.div
                variants={stagger}
                initial="hidden"
                animate="show"
                className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3"
              >
                {displayed.map((item) => (
                  <ResumeCard
                    key={item.mongo_id || item.id}
                    item={item}
                    onClick={() =>
                      navigate(`/results/${item.mongo_id || item.id}`)
                    }
                  />
                ))}
              </motion.div>
            </>
          )}

          {/* ── Upload CTA ── */}
          {!loading && (
            <motion.div
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2 }}
              className="mt-10 pt-6 border-t border-border/35 flex justify-center"
            >
              <button
                onClick={() => navigate("/upload")}
                className="
                  px-5 py-2.5 rounded-xl border border-border bg-card/70
                  text-sm font-semibold text-foreground
                  inline-flex items-center gap-2
                  hover:border-primary/35 hover:text-primary transition-colors
                "
              >
                <ArrowUpRight className="w-4 h-4" strokeWidth={1.75} />
                Upload Another Resume
              </button>
            </motion.div>
          )}

        </div>
      </div>
    </PageTransition>
  );
}