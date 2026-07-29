// Fetch client for the FastAPI backend.
// CORS on the backend already allows the Vite dev origin, so we call it directly.
import type {
  DocumentDetail,
  DocumentSummary,
  DecisionResult,
  DocType,
  OcrEngine,
  OCRResult,
  QualityReport,
  StructuredResult,
} from "@/lib/types";

const API_BASE_URL: string =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export interface HealthResponse {
  status: string;
}

/**
 * The backend returns server-relative asset URLs (e.g. `/files/<id>/pages/...`).
 * The frontend runs on a different origin with no proxy, so every rendered
 * asset must be absolutized through this helper.
 */
export function fileUrl(path?: string | null): string | undefined {
  if (!path) return undefined;
  if (/^https?:\/\//.test(path)) return path;
  return `${API_BASE_URL}${path.startsWith("/") ? "" : "/"}${path}`;
}

/** Raised on a non-2xx response; carries the HTTP status for UI handling. */
export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

interface RequestOpts {
  method?: string;
  query?: Record<string, string | number | boolean | undefined>;
  body?: BodyInit;
  signal?: AbortSignal;
}

async function request<T>(path: string, opts: RequestOpts = {}): Promise<T> {
  const { method = "GET", query, body, signal } = opts;
  const qs = query
    ? "?" +
      Object.entries(query)
        .filter(([, v]) => v !== undefined)
        .map(([k, v]) => `${k}=${encodeURIComponent(String(v))}`)
        .join("&")
    : "";
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}${qs}`, { method, body, signal });
  } catch {
    throw new ApiError(0, "Cannot reach the backend — is it running on :8000?");
  }
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const data = (await res.json()) as { detail?: string };
      if (data?.detail) detail = data.detail;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, detail);
  }
  // 204 No Content (e.g. DELETE) and any non-JSON/empty body have nothing to
  // parse. Guarding on content-type (not just Content-Length, which proxies may
  // omit on chunked responses) keeps res.json() from throwing on an empty body.
  if (
    res.status === 204 ||
    res.headers.get("content-length") === "0" ||
    !res.headers.get("content-type")?.includes("application/json")
  ) {
    return undefined as T;
  }
  return (await res.json()) as T;
}

export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

// --- documents ---------------------------------------------------------------

export async function uploadDocument(
  file: File,
  docType?: DocType,
): Promise<DocumentDetail> {
  const form = new FormData();
  form.append("file", file);
  if (docType) form.append("doc_type", docType);
  return request<DocumentDetail>("/documents", { method: "POST", body: form });
}

export async function getDocument(id: string): Promise<DocumentDetail> {
  return request<DocumentDetail>(`/documents/${id}`);
}

export async function listDocuments(): Promise<DocumentSummary[]> {
  return request<DocumentSummary[]>("/documents");
}

export async function deleteDocument(id: string): Promise<void> {
  await request<void>(`/documents/${id}`, { method: "DELETE" });
}

export async function deleteAllDocuments(): Promise<void> {
  await request<void>("/documents", { method: "DELETE" });
}

// --- persisted stage results (GET; 404 when a stage hasn't run) ---------------

export async function getPrescan(id: string): Promise<QualityReport> {
  return request<QualityReport>(`/documents/${id}/prescan`);
}

export async function getOcr(
  id: string,
  engine: OcrEngine,
): Promise<OCRResult> {
  return request<OCRResult>(`/documents/${id}/ocr`, { query: { engine } });
}

export async function getStructure(id: string): Promise<StructuredResult> {
  return request<StructuredResult>(`/documents/${id}/structure`);
}

export async function getDecision(id: string): Promise<DecisionResult> {
  return request<DecisionResult>(`/documents/${id}/decide`);
}

// --- pipeline stages (live engines) ------------------------------------------

export async function runPrescan(
  id: string,
  opts: { deskew?: boolean; clean?: boolean } = {},
): Promise<QualityReport> {
  return request<QualityReport>(`/documents/${id}/prescan`, {
    method: "POST",
    query: { deskew: opts.deskew ?? true, clean: opts.clean ?? true },
  });
}

export async function runOcr(
  id: string,
  engine: OcrEngine,
): Promise<OCRResult> {
  return request<OCRResult>(`/documents/${id}/ocr`, {
    method: "POST",
    query: { engine },
  });
}

export async function runStructure(
  id: string,
  p: { docType: DocType; ocrEngine: OcrEngine },
): Promise<StructuredResult> {
  return request<StructuredResult>(`/documents/${id}/structure`, {
    method: "POST",
    query: { doc_type: p.docType, ocr_engine: p.ocrEngine },
  });
}

export async function runDecide(id: string): Promise<DecisionResult> {
  return request<DecisionResult>(`/documents/${id}/decide`, { method: "POST" });
}

export { API_BASE_URL };
