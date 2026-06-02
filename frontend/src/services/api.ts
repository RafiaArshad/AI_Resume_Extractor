// src/services/api.ts
// Central API service layer — all backend communication goes through here.

import axios, { AxiosError } from "axios";
import type {
  UploadResponse,
  GetResumeResponse,
  ListResponse,
  DeleteResponse,
} from "@/types/resume";

// ─────────────────────────────────────────────────────────────
// Config
// ─────────────────────────────────────────────────────────────

const ENV = import.meta.env as Record<string, string | undefined>;

export const API_BASE =
  ENV.VITE_API_BASE ?? "http://localhost:8000";

const RESUME_BASE = `${API_BASE}/api/resume`;

/**
 * Upload instance — no client-side timeout.
 * LLM parsing may take time → backend timeout handles it.
 */
const api = axios.create({
  baseURL: API_BASE,
  timeout: 0,
});

/**
 * Fast read-only instance (DB queries)
 */
const apiRead = axios.create({
  baseURL: API_BASE,
  timeout: 30_000,
});

// ─────────────────────────────────────────────────────────────
// Error helper
// ─────────────────────────────────────────────────────────────

function extractMessage(
  error: unknown,
  fallback = "An unexpected error occurred.",
): never {
  if (axios.isAxiosError(error)) {
    const axErr = error as AxiosError<{ error?: string; message?: string }>;

    const msg =
      axErr.response?.data?.error ??
      axErr.response?.data?.message ??
      axErr.message;

    throw new Error(msg || fallback);
  }

  if (error instanceof Error) throw error;

  throw new Error(fallback);
}

// ─────────────────────────────────────────────────────────────
// Upload resume
// POST /api/resume/upload
// ─────────────────────────────────────────────────────────────

export async function uploadResume(
  file: File,
  onProgress?: (pct: number) => void,
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await api.post<UploadResponse>(
      `${RESUME_BASE}/upload`,
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (event) => {
          if (onProgress && event.total) {
            const pct = Math.round((event.loaded / event.total) * 100);
            onProgress(pct);
          }
        },
      },
    );

    if (!response.data.success) {
      throw new Error(response.data.error ?? "Upload failed.");
    }

    return response.data;
  } catch (err) {
    extractMessage(err, "Upload failed. Please try again.");
  }

  // Ensures TypeScript never complains about missing return
  throw new Error("Upload failed.");
}



// ─────────────────────────────────────────────────────────────
// Get single resume
// GET /api/resume/:resumeId
// ─────────────────────────────────────────────────────────────

export async function getResume(
  resumeId: string,
): Promise<GetResumeResponse> {
  try {
    const response = await apiRead.get<GetResumeResponse>(
      `${RESUME_BASE}/${resumeId}`,
    );

    if (!response.data.success) {
      throw new Error(response.data.error ?? "Resume not found.");
    }

    return response.data;
  } catch (err) {
    extractMessage(err, "Could not load resume data.");
  }

  throw new Error("Could not load resume data.");
}

// ─────────────────────────────────────────────────────────────
// List resumes (paginated)
// GET /api/resume/list?skip=0&limit=20
// ─────────────────────────────────────────────────────────────

export async function listResumes(
  skip = 0,
  limit = 20,
): Promise<ListResponse> {
  try {
    const response = await apiRead.get<ListResponse>(
      `${RESUME_BASE}/list`,
      {
        params: { skip, limit },
      },
    );

    if (!response.data.success) {
      throw new Error(response.data.error ?? "Could not list resumes.");
    }

    return response.data;
  } catch (err) {
    extractMessage(err, "Could not fetch resume list.");
  }

  throw new Error("Could not fetch resume list.");
}

// ─────────────────────────────────────────────────────────────
// Delete resume
// DELETE /api/resume/:resumeId
// ─────────────────────────────────────────────────────────────

export async function deleteResume(
  resumeId: string,
): Promise<DeleteResponse> {
  try {
    const response = await apiRead.delete<DeleteResponse>(
      `${RESUME_BASE}/${resumeId}`,
    );

    if (!response.data.success) {
      throw new Error(response.data.error ?? "Could not delete resume.");
    }

    return response.data;
  } catch (err) {
    extractMessage(err, "Delete failed. Please try again.");
  }

  throw new Error("Delete failed.");
}


// ── ADD THESE ──────────────────────────────────────────────────

export async function ListResumes(skip = 0, limit = 100) {
  const res = await fetch(`${RESUME_BASE}/list?skip=${skip}&limit=${limit}`);
  return res.json();
}

export async function searchResumes(params: {
  name?:    string;
  keyword?: string;
  level?:   string;
  field?:   string;
  skip?:    number;
  limit?:   number;
}) {
  const q = new URLSearchParams();
  if (params.name)    q.set("name",    params.name);
  if (params.keyword) q.set("keyword", params.keyword);
  if (params.level)   q.set("level",   params.level);
  if (params.field)   q.set("field",   params.field);
  q.set("skip",  String(params.skip  ?? 0));
  q.set("limit", String(params.limit ?? 100));

  const res = await fetch(`${RESUME_BASE}/search?${q}`);
  return res.json();

}