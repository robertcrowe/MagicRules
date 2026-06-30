import { useState } from "react";
import type { Citation } from "../api/client";

interface CitationCardProps {
  citation: Citation;
  index: number;
}

export function CitationCard({ citation, index: _index }: CitationCardProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="citation-card">
      <div className="citation-header">
        <span className="rule-badge">Rule {citation.rule_number}</span>
        <button
          className="expand-btn"
          onClick={() => setExpanded((prev) => !prev)}
          aria-expanded={expanded}
        >
          {expanded ? "Hide" : "View Rule Text"}
        </button>
      </div>
      {expanded && <blockquote className="rule-quote">{citation.quoted_text}</blockquote>}
    </div>
  );
}
