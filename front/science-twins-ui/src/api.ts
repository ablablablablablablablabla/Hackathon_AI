import type { AnalyzeResponse } from "./types";

const API_URL = "http://127.0.0.1:8000/api/analyze";

export async function analyze(
  text: string,
  mode: "plagiarism" | "doppelganger",
  file?: File | null
): Promise<AnalyzeResponse> {
  let body: BodyInit;
  let headers: HeadersInit = {};

  if (file) {
    const formData = new FormData();
    formData.append("mode", mode);
    formData.append("file", file);
    body = formData;
    // Don't set Content-Type header - let browser set it with boundary
  } else {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify({ text, mode });
  }

  const res = await fetch(API_URL, {
    method: "POST",
    headers,
    body,
  });

  if (!res.ok) {
    throw new Error(`Request failed with status ${res.status}`);
  }

  return res.json();
}
