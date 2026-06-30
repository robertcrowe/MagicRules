import type { AskResponse } from "../api/client";
import { CitationCard } from "./CitationCard";

interface AnswerDisplayProps {
  answer: AskResponse;
}

export function AnswerDisplay({ answer }: AnswerDisplayProps) {
  return (
    <div className="answer-section">
      {!answer.has_exact_match && answer.disclaimer && (
        <div className="disclaimer" role="alert">
          <span className="disclaimer-icon">⚠</span>
          {answer.disclaimer}
        </div>
      )}

      <div className="answer-card">
        <h3 className="answer-label">Answer</h3>
        <p className="answer-text">{answer.answer_text}</p>

        {answer.citations.length > 0 && (
          <div className="citations-section">
            <h4 className="citations-label">Rule Citations ({answer.citations.length})</h4>
            <div className="citations-list">
              {answer.citations.map((citation, index) => (
                <CitationCard key={citation.rule_number} citation={citation} index={index} />
              ))}
            </div>
          </div>
        )}

        <div className="answer-meta">
          Answer generated in {(answer.latency_ms / 1000).toFixed(1)}s
        </div>
      </div>
    </div>
  );
}
