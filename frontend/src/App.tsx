import { QuestionForm } from "./components/QuestionForm";
import { AnswerDisplay } from "./components/AnswerDisplay";
import { useQuestion } from "./hooks/useQuestion";
import "./App.css";

export default function App() {
  const { answer, loading, error, submit } = useQuestion();

  return (
    <div className="app-wrapper">
      <header>
        <div className="header-content">
          <a href="/" className="logo">
            <div className="logo-icon">⚖</div>
            MagicRules
          </a>
          <nav className="nav">
            <a href="https://magic.wizards.com/en/rules" target="_blank" rel="noreferrer">
              Official Rules
            </a>
          </nav>
        </div>
      </header>

      <main>
        <section className="hero">
          <p className="subtitle">Magic: The Gathering</p>
          <h1>Rules Answered Instantly</h1>
          <p>
            Ask any rules question and get grounded answers with exact rule citations from the
            official Comprehensive Rules.
          </p>
        </section>

        <QuestionForm onSubmit={submit} loading={loading} />

        {error && (
          <div className="error-banner" role="alert">
            {error}
          </div>
        )}

        {answer && <AnswerDisplay answer={answer} />}
      </main>
    </div>
  );
}
