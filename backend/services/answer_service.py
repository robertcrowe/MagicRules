import logging

from anthropic import AsyncAnthropic

from backend.config import settings
from backend.models import Answer, Citation, Rule

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Magic: The Gathering rules expert and rule lawyer.
Answer the user's question using ONLY the retrieved rules provided below.

Requirements:
1. Only cite rules from the provided list — do not reference any other rules.
2. Include the exact rule number (e.g. "100.1a") for each citation.
3. Quote the relevant text from the rule exactly as it appears.
4. If no relevant rule exists in the provided list, say so plainly and set has_exact_match to false.
5. When has_exact_match is false, include a disclaimer explaining the situation.
"""

ANSWER_TOOL_SCHEMA: dict[str, object] = {
    "name": "answer_question",
    "description": "Provide a structured answer with citations from the retrieved rules.",
    "input_schema": {
        "type": "object",
        "properties": {
            "answer_text": {
                "type": "string",
                "description": "Clear answer to the question.",
            },
            "citations": {
                "type": "array",
                "description": "Citations from the retrieved rules only.",
                "items": {
                    "type": "object",
                    "properties": {
                        "rule_number": {
                            "type": "string",
                            "description": "Exact rule number, e.g. '100.1a'.",
                        },
                        "quoted_text": {
                            "type": "string",
                            "description": "Exact quote from the rule text.",
                        },
                    },
                    "required": ["rule_number", "quoted_text"],
                },
            },
            "has_exact_match": {
                "type": "boolean",
                "description": "True if at least one retrieved rule directly answers the question.",
            },
            "disclaimer": {
                "type": "string",
                "description": "Set when has_exact_match is false to explain the limitation.",
            },
        },
        "required": ["answer_text", "citations", "has_exact_match"],
    },
}


async def generate_answer(question: str, retrieved_rules: list[Rule]) -> Answer:
    """Generate a grounded answer from retrieved rules using Claude."""
    if not settings.ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY is not configured")

    client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    rules_context = "\n\n".join(
        f"Rule {r.rule_number} — {r.section_title}:\n{r.full_text}" for r in retrieved_rules
    )
    user_message = f"Question: {question}\n\nRetrieved Rules:\n{rules_context}"

    valid_rule_numbers = {r.rule_number for r in retrieved_rules}

    try:
        response = await client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=settings.MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
            tools=[ANSWER_TOOL_SCHEMA],  # type: ignore[list-item]
            tool_choice={"type": "tool", "name": "answer_question"},
        )
    except Exception as exc:
        logger.error("Anthropic API error: %s", exc)
        raise RuntimeError(f"Failed to generate answer: {exc}") from exc

    for block in response.content:
        if block.type == "tool_use":
            raw: dict[str, object] = block.input  # type: ignore[assignment]
            raw_citations = raw.get("citations", [])
            citations: list[Citation] = []
            if isinstance(raw_citations, list):
                for c in raw_citations:
                    if isinstance(c, dict):
                        citations.append(
                            Citation(
                                rule_number=str(c.get("rule_number", "")),
                                quoted_text=str(c.get("quoted_text", "")),
                            )
                        )
            # Remove hallucinated citations not in the retrieved set
            valid_citations = [c for c in citations if c.rule_number in valid_rule_numbers]

            has_match = len(valid_citations) > 0
            raw_disclaimer = raw.get("disclaimer")
            disclaimer: str | None = (
                str(raw_disclaimer) if isinstance(raw_disclaimer, str) else None
            )
            if not has_match and not disclaimer:
                disclaimer = (
                    "I could not find an exact rule for this question. "
                    "Here is the closest general rule:"
                )

            return Answer(
                answer_text=str(raw.get("answer_text", "")),
                citations=valid_citations,
                has_exact_match=has_match,
                disclaimer=disclaimer if not has_match else None,
            )

    logger.error("No tool_use block found in Anthropic response")
    return Answer(
        answer_text="Failed to generate a structured answer.",
        citations=[],
        has_exact_match=False,
        disclaimer="An unexpected error occurred while generating the answer.",
    )
