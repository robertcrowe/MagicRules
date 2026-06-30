import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { AnswerDisplay } from "../components/AnswerDisplay";
import type { AskResponse } from "../api/client";

const mockAnswer: AskResponse = {
  question: "What is the stack?",
  answer_text: "The stack is a zone where spells and abilities await resolution.",
  citations: [
    { rule_number: "405.1", quoted_text: "The stack is a zone." },
    { rule_number: "405.2", quoted_text: "Triggered abilities go on the stack." },
  ],
  has_exact_match: true,
  disclaimer: null,
  latency_ms: 1500,
};

describe("AnswerDisplay", () => {
  it("displays the answer text", () => {
    render(<AnswerDisplay answer={mockAnswer} />);
    expect(
      screen.getByText("The stack is a zone where spells and abilities await resolution.")
    ).toBeInTheDocument();
  });

  it("renders citations as a list", () => {
    render(<AnswerDisplay answer={mockAnswer} />);
    expect(screen.getByText("Rule 405.1")).toBeInTheDocument();
    expect(screen.getByText("Rule 405.2")).toBeInTheDocument();
  });

  it("expands citation to show quoted text on button click", () => {
    render(<AnswerDisplay answer={mockAnswer} />);
    const buttons = screen.getAllByText("View Rule Text");
    fireEvent.click(buttons[0]);
    expect(screen.getByText("The stack is a zone.")).toBeInTheDocument();
  });

  it("displays disclaimer when has_exact_match is false", () => {
    const noMatchAnswer: AskResponse = {
      ...mockAnswer,
      has_exact_match: false,
      disclaimer: "I could not find an exact rule.",
    };
    render(<AnswerDisplay answer={noMatchAnswer} />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText(/could not find an exact rule/i)).toBeInTheDocument();
  });

  it("shows latency_ms at the bottom", () => {
    render(<AnswerDisplay answer={mockAnswer} />);
    expect(screen.getByText(/1\.5s/)).toBeInTheDocument();
  });
});
