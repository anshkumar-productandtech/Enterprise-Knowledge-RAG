// Server-only helper for calling the FastAPI backend. The browser never talks
// to the backend directly, so the API token and backend address stay private.

const BACKEND_URL = (process.env.BACKEND_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

export function backendFetch(path: string, init: RequestInit & { clientIp?: string } = {}) {
  const headers = new Headers(init.headers);
  const token = process.env.DEMO_API_TOKEN;
  if (token) headers.set("authorization", `Bearer ${token}`);
  if (init.clientIp) headers.set("x-forwarded-for", init.clientIp);
  return fetch(`${BACKEND_URL}${path}`, { ...init, headers, cache: "no-store" });
}

export function clientIp(req: Request): string {
  return req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || "local";
}

// Messages a visitor may see. Upstream error bodies are never passed through.
export function messageForStatus(status: number): string {
  if (status === 429) return "That's a lot of questions in one minute. Wait a moment, then ask again.";
  if (status === 413) return "That question is too long. Shorten it to a sentence or two.";
  if (status === 400 || status === 422) return "That question couldn't be read. Rephrase it and ask again.";
  return "The assistant isn't responding. Try again in a minute.";
}
