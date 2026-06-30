import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

const schema = z.object({
  question: z
    .string()
    .min(1, "Question is required")
    .max(500, "Question must be 500 characters or fewer"),
});

type FormValues = z.infer<typeof schema>;

interface QuestionFormProps {
  onSubmit: (question: string) => Promise<void>;
  loading: boolean;
}

export function QuestionForm({ onSubmit, loading }: QuestionFormProps) {
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const questionValue = watch("question") ?? "";

  const submit = async (values: FormValues) => {
    await onSubmit(values.question);
  };

  return (
    <div className="question-section">
      <div className="question-card">
        <h2>Ask a Rules Question</h2>
        <form onSubmit={handleSubmit(submit)} noValidate>
          <div className="input-group">
            <input
              {...register("question")}
              type="text"
              className="question-input"
              placeholder="e.g. What happens when two triggered abilities trigger at the same time?"
              disabled={loading}
              maxLength={500}
            />
            <button type="submit" className="submit-btn" disabled={loading}>
              {loading ? (
                <>
                  <span className="spinner" aria-hidden="true" />
                  Asking...
                </>
              ) : (
                "Ask"
              )}
            </button>
          </div>

          {errors.question && (
            <p className="field-error" role="alert">
              {errors.question.message}
            </p>
          )}

          <div className="char-counter" aria-live="polite">
            {questionValue.length}/500
          </div>
        </form>
      </div>
    </div>
  );
}
