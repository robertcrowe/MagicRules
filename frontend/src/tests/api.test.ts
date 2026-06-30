import { describe, it, expect, vi, beforeEach } from "vitest";
import { askQuestion } from "../api/client";

const mockResponse = {
  question: "What is the stack?",
  answer_text: "The stack is a zone.",
  citations: [{ rule_number: "405.1", quoted_text: "The stack is a zone." }],
  has_exact_match: true,
  disclaimer: null,
  latency_ms: 1200,
};

describe("askQuestion", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("calls the correct endpoint with POST and JSON body", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => mockResponse }));

    const result = await askQuestion("What is the stack?");
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/ask"),
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: "What is the stack?" }),
      })
    );
    expect(result.answer_text).toBe("The stack is a zone.");
  });

  it("parses the response correctly", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => mockResponse }));

    const result = await askQuestion("What is the stack?");
    expect(result.has_exact_match).toBe(true);
    expect(result.citations).toHaveLength(1);
    expect(result.citations[0].rule_number).toBe("405.1");
  });

  it("throws on network failure", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("Network error")));

    await expect(askQuestion("test")).rejects.toThrow("Network error");
  });

  it("throws on non-OK response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 500, text: async () => "Internal server error" })
    );

    await expect(askQuestion("test")).rejects.toThrow("API error 500");
  });
});
