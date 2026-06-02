// src/pages/UploadPage.tsx
import { useState, useCallback, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  Upload, X, CheckCircle, Loader2,
  AlertCircle, ArrowRight, Sparkles, Clock,
} from "lucide-react";
import PageTransition from "@/components/layout/PageTransition";
import { uploadResume } from "@/services/api";

const ACCEPTED_TYPES = [
  "application/pdf",
  "application/msword",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
];
const ACCEPTED_EXT = [".pdf", ".doc", ".docx"];

// Rotating status messages shown while the server works
const PARSE_STAGES = [
  { pct: 0,  msg: "Uploading file…" },
  { pct: 15, msg: "Extracting text from document…" },
  { pct: 30, msg: "Identifying resume sections…" },
  { pct: 50, msg: "Parsing skills, education & experience…" },
  { pct: 65, msg: "Running AI analysis (may take 1–2 min)…" },
  { pct: 80, msg: "Scoring skills and classifying domain…" },
  { pct: 92, msg: "Saving results…" },
];

const TIPS = [
  "Works best with ATS-friendly PDF resumes",
  "Supports PDF and Word (.docx) formats",
  "AI extracts skills, education & experience",
  "Results are saved and accessible via URL",
];

export default function UploadPage() {
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);

  const [file,       setFile]       = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploading,  setUploading]  = useState(false);
  const [progress,   setProgress]   = useState(0);
  const [statusMsg,  setStatusMsg]  = useState("");
  const [elapsed,    setElapsed]    = useState(0);
  const [error,      setError]      = useState("");

  // ── File validation ────────────────────────────────────────────
  const handleFile = useCallback((selected: File) => {
    const ext = "." + (selected.name.split(".").pop() ?? "").toLowerCase();
    if (!ACCEPTED_TYPES.includes(selected.type) && !ACCEPTED_EXT.includes(ext)) {
      setError("Only PDF or Word (.docx) files are supported.");
      return;
    }
    if (selected.size > 10 * 1024 * 1024) {
      setError("File size must be under 10 MB.");
      return;
    }
    setFile(selected);
    setError("");
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files?.[0]) handleFile(e.dataTransfer.files[0]);
  }, [handleFile]);

  const formatSize = (b: number) =>
    b < 1024 ? `${b} B`
    : b < 1024 * 1024 ? `${(b / 1024).toFixed(1)} KB`
    : `${(b / (1024 * 1024)).toFixed(1)} MB`;

  // ── Upload ─────────────────────────────────────────────────────
  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setProgress(0);
    setElapsed(0);
    setError("");
    setStatusMsg(PARSE_STAGES[0].msg);

    // ── elapsed timer ─────────────────────────────────────────
    const startTime  = Date.now();
    const elapsedRef = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);

    // ── smooth fake progress ──────────────────────────────────
    let fakeProgress = 0;
    const progressRef = setInterval(() => {
      fakeProgress = Math.min(fakeProgress + Math.random() * 3, 90);
      setProgress(fakeProgress);
      // Update status message based on progress band
      const stage = [...PARSE_STAGES].reverse().find(s => fakeProgress >= s.pct);
      if (stage) setStatusMsg(stage.msg);
    }, 400);

    try {
      const data = await uploadResume(file, (pct) => {
        // Once actual upload progress arrives, jump ahead
        if (pct > 0) {
          fakeProgress = Math.max(fakeProgress, pct * 0.15); // upload = first 15%
          setProgress(fakeProgress);
        }
      });

      clearInterval(progressRef);
      clearInterval(elapsedRef);
      setProgress(100);
      setStatusMsg("Done! Redirecting…");

      setTimeout(() => navigate(`/results/${data.resume_id}`), 600);

    } catch (err) {
      clearInterval(progressRef);
      clearInterval(elapsedRef);
      const msg = err instanceof Error ? err.message : "Upload failed. Please try again.";
      setError(msg);
      setUploading(false);
      setProgress(0);
      setStatusMsg("");
      setElapsed(0);
    }
  };

  const formatElapsed = (s: number) =>
    s < 60 ? `${s}s` : `${Math.floor(s / 60)}m ${s % 60}s`;

  return (
    <PageTransition>
      <div className="min-h-screen pt-20 pb-16">
        <div className="container mx-auto px-4 max-w-2xl">

          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -16 }} animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45 }}
            className="text-center mb-8"
          >
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full
                            bg-primary/10 border border-primary/20 text-primary text-sm font-medium mb-4">
              <Sparkles className="w-3.5 h-3.5" />
              AI-Powered Resume Analysis
            </div>
            <h1 className="text-3xl md:text-4xl font-bold mb-2">Upload Your Resume</h1>
            <p className="text-muted-foreground text-sm">
              PDF or DOCX · Up to 10 MB · Results in seconds
            </p>
          </motion.div>

          {/* Main card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, delay: 0.1 }}
            className="glass-card rounded-2xl p-6 space-y-5"
          >
            {/* Drop zone */}
            <div
              className={`relative border-2 border-dashed rounded-xl p-10 text-center
                          transition-all duration-200 select-none
                          ${uploading ? "pointer-events-none opacity-75" : "cursor-pointer"}
                          ${dragActive
                            ? "border-primary bg-primary/8 scale-[1.01]"
                            : file
                              ? "border-green-400/60 bg-green-500/5"
                              : "border-border hover:border-primary/50 hover:bg-primary/4"
                          }`}
              onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
              onDragLeave={() => setDragActive(false)}
              onDrop={handleDrop}
              onClick={() => !uploading && inputRef.current?.click()}
            >
              <input
                ref={inputRef} type="file" className="hidden"
                accept=".pdf,.doc,.docx"
                onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
              />

              <AnimatePresence mode="wait">
                {file ? (
                  <motion.div key="file"
                    initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    className="flex flex-col items-center gap-2"
                  >
                    <div className="w-14 h-14 rounded-2xl bg-green-500/15 border border-green-400/30
                                    flex items-center justify-center mb-1">
                      <CheckCircle className="w-7 h-7 text-green-500" />
                    </div>
                    <p className="font-semibold text-base">{file.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {formatSize(file.size)} · {file.name.split(".").pop()?.toUpperCase()}
                    </p>
                    {!uploading && (
                      <button
                        onClick={(e) => { e.stopPropagation(); setFile(null); setError(""); }}
                        className="mt-1 flex items-center gap-1 text-xs text-muted-foreground
                                   hover:text-destructive transition-colors"
                      >
                        <X className="w-3 h-3" /> Remove file
                      </button>
                    )}
                  </motion.div>
                ) : (
                  <motion.div key="empty"
                    initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                    className="flex flex-col items-center gap-3"
                  >
                    <div className="w-14 h-14 rounded-2xl gradient-bg flex items-center justify-center mb-1">
                      <Upload className="w-6 h-6 text-primary-foreground" />
                    </div>
                    <div>
                      <p className="font-semibold text-base">
                        {dragActive ? "Drop it here!" : "Drag & drop your resume"}
                      </p>
                      <p className="text-sm text-muted-foreground mt-1">
                        or <span className="text-primary font-medium">browse files</span>
                      </p>
                    </div>
                    <div className="flex gap-2 mt-1">
                      {["PDF", "DOCX"].map((t) => (
                        <span key={t} className="px-2.5 py-1 text-xs rounded-full bg-secondary
                                                  text-secondary-foreground font-medium border border-border/50">
                          {t}
                        </span>
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Error */}
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                  className="flex items-start gap-2.5 p-3.5 rounded-xl
                             bg-destructive/8 border border-destructive/20 text-destructive"
                >
                  <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                  <span className="text-sm">{error}</span>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Progress + elapsed */}
            <AnimatePresence>
              {uploading && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                  className="space-y-3"
                >
                  {/* Status row */}
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-muted-foreground font-medium flex items-center gap-1.5">
                      <Loader2 className="w-3.5 h-3.5 animate-spin text-primary" />
                      {statusMsg}
                    </span>
                    <span className="tabular-nums font-semibold text-primary">
                      {Math.round(progress)}%
                    </span>
                  </div>

                  {/* Bar */}
                  <div className="h-2.5 rounded-full bg-secondary overflow-hidden">
                    <motion.div
                      className="h-full gradient-bg rounded-full"
                      animate={{ width: `${progress}%` }}
                      transition={{ duration: 0.4, ease: "easeOut" }}
                    />
                  </div>

                  {/* Elapsed + hint */}
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {formatElapsed(elapsed)} elapsed
                    </span>
                    {elapsed >= 20 && (
                      <motion.span
                        initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                        className="italic"
                      >
                        AI parsing on CPU can take 1–2 min — please wait…
                      </motion.span>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Submit */}
            <button
              onClick={handleUpload}
              disabled={!file || uploading}
              className="w-full py-3 rounded-xl gradient-bg text-primary-foreground font-semibold
                         flex items-center justify-center gap-2.5 text-sm
                         disabled:opacity-50 disabled:cursor-not-allowed
                         hover:opacity-90 active:scale-[0.99] transition-all duration-150 shadow-md"
            >
              {uploading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Analysing Resume…
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Parse Resume
                  <ArrowRight className="w-4 h-4 ml-auto" />
                </>
              )}
            </button>
          </motion.div>

          {/* Feature tips */}
          <motion.div
            initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.45 }}
            className="mt-6 grid grid-cols-2 gap-3"
          >
            {TIPS.map((tip, i) => (
              <div key={i}
                   className="flex items-start gap-2.5 p-3.5 rounded-xl glass-card border text-sm">
                <CheckCircle className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                <span className="text-muted-foreground leading-snug">{tip}</span>
              </div>
            ))}
          </motion.div>

        </div>
      </div>
    </PageTransition>
  );
}
