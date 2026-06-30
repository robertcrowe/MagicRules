import { useState } from "react";
import { askQuestion } from "../api/client";
import type { AskResponse } from "../api/client";

interface UseQuestionReturn {
  answer: AskResponse | null;
  loading: boolean;
  error: string | null;
  submit: (question: string) => Promise<void>;
}

export function useQuestion(): UseQuestionReturn {
  const [answer, setAnswer] = useState<AskResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (question: string) => {
    setLoading(true);
    setError(null);
    try {
      const result = await askQuestion(question);
      setAnswer(result);
    } catch (err) {
      const message = err instanceof Error ? err.message : "An unexpected error occurred";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return { answer, loading, error, submit };
}
