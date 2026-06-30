const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export interface Citation {
  rule_number: string;
  quoted_text: string;
}

export interface AskResponse {
  question: string;
  answer_text: string;
  citations: Citation[];
  has_exact_match: boolean;
  disclaimer: string | null;
  latency_ms: number;
}

export async function askQuestion(question: string): Promise<AskResponse> {
  const res = await fetch(`${API_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });

  if (!res.ok) {
    const detail = await res.text().catch(() => "Unknown error");
    throw new Error(`API error ${res.status}: ${detail}`);
  }

  return res.json() as Promise<AskResponse>;
}
