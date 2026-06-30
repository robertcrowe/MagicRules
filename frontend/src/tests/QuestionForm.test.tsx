import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { QuestionForm } from "../components/QuestionForm";

describe("QuestionForm", () => {
  it("renders with a text input and submit button", () => {
    render(<QuestionForm onSubmit={vi.fn()} loading={false} />);
    expect(screen.getByRole("textbox")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /ask/i })).toBeInTheDocument();
  });

  it("shows validation error for empty submission", async () => {
    render(<QuestionForm onSubmit={vi.fn()} loading={false} />);
    fireEvent.click(screen.getByRole("button", { name: /ask/i }));
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
  });

  it("character counter updates as user types", () => {
    render(<QuestionForm onSubmit={vi.fn()} loading={false} />);
    const input = screen.getByRole("textbox");
    fireEvent.change(input, { target: { value: "Hello" } });
    expect(screen.getByText("5/500")).toBeInTheDocument();
  });

  it("disables submit button while loading", () => {
    render(<QuestionForm onSubmit={vi.fn()} loading={true} />);
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("calls onSubmit with the question on valid submit", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<QuestionForm onSubmit={onSubmit} loading={false} />);
    const input = screen.getByRole("textbox");
    fireEvent.change(input, { target: { value: "What is the stack?" } });
    fireEvent.click(screen.getByRole("button", { name: /ask/i }));
    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith("What is the stack?");
    });
  });
});
