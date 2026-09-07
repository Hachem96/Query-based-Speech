/**
 * Thin typed client for the FastAPI backend (backend/api/main.py).
 *
 * `NEXT_PUBLIC_API_BASE` is read on both the server and the client, so the URL
 * must be reachable from both.
 */
export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, "") || "http://localhost:8000";

export type Video = {
  id: number;
  name: string;
  subject: string | null;
  year: number | null;
  caption: string | null;
  coverUrl: string | null;
  videoUrl: string | null;
  transcriptionUrl: string | null;
  summaryUrl: string | null;
  translationUrl: string | null;
};

export type Book = {
  id: number;
  title: string | null;
  author: string | null;
  year: number | null;
  caption: string | null;
  pdfUrl: string | null;
  coverUrl: string | null;
};

export type FilterOptions = { subjects: string[]; years: number[] };

export type InferenceResult = {
  startTimeStamp: number;
  endTimeStamp: number;
  duration: number;
};

/** Turn a backend-relative `/media/...` path into an absolute URL. */
export function mediaUrl(path: string | null | undefined): string | null {
  if (!path) return null;
  if (/^https?:\/\//.test(path)) return path;
  return `${API_BASE}${path.startsWith("/") ? "" : "/"}${path}`;
}

async function getJSON<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    // Catalog data changes rarely; revalidate on the server every 60s.
    next: { revalidate: 60 },
    ...init,
  });
  if (!res.ok) {
    throw new Error(`API ${path} -> ${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export function listVideos(params: { subject?: string; year?: string } = {}) {
  const qs = new URLSearchParams();
  if (params.subject) qs.set("subject", params.subject);
  if (params.year) qs.set("year", params.year);
  const suffix = qs.toString() ? `?${qs}` : "";
  return getJSON<Video[]>(`/api/videos${suffix}`);
}

export const getVideo = (id: number | string) => getJSON<Video>(`/api/videos/${id}`);
export const listBooks = () => getJSON<Book[]>(`/api/books`);
export const getBook = (id: number | string) => getJSON<Book>(`/api/books/${id}`);
export const getFilterOptions = () => getJSON<FilterOptions>(`/api/filters`);

/** Run retrieval for `query` against `videoName`. Client-side call. */
export async function runInference(
  videoName: string,
  query: string,
): Promise<InferenceResult> {
  const res = await fetch(`${API_BASE}/inference/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ videoName, query }),
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(`Inference failed (${res.status}). ${detail}`);
  }
  const body = (await res.json()) as { success: boolean; result: InferenceResult };
  return body.result;
}
