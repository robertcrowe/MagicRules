import logging
import re
import urllib.request

from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.config import settings
from backend.models import Rule

logger = logging.getLogger(__name__)

# Matches rule numbers like "603.1", "107.3k" at start of a line
RULE_NUMBER_PATTERN = re.compile(r"^\d+\.\d+[a-z]?", re.MULTILINE)


def _download_or_read(url_or_path: str) -> str:
    if url_or_path.startswith(("http://", "https://")):
        logger.info("Downloading rules from %s", url_or_path)
        req = urllib.request.Request(url_or_path, headers={"User-Agent": "MagicRules/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data: bytes = resp.read()
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            return data.decode("latin-1")
    logger.info("Reading rules from local file %s", url_or_path)
    with open(url_or_path, encoding="utf-8", errors="replace") as f:
        return f.read()


def _extract_section_title(chunk: str) -> str:
    for line in chunk.split("\n")[:10]:
        stripped = line.strip()
        if re.match(r"^\d+\.", stripped) and 5 < len(stripped) < 120:
            return stripped
    return "General Rules"


def parse_rules_file() -> list[Rule]:
    """Parse the Comprehensive Rules file and return a list of Rule objects."""
    text = _download_or_read(settings.RULES_FILE_URL)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " "],
    )
    chunks = splitter.split_text(text)

    rules: list[Rule] = []
    seen: set[str] = set()
    skipped = 0

    for chunk in chunks:
        match = RULE_NUMBER_PATTERN.search(chunk)
        if not match:
            skipped += 1
            continue

        rule_number = match.group(0).strip()
        if not rule_number:
            skipped += 1
            continue

        if rule_number in seen:
            continue
        seen.add(rule_number)

        rule_text = chunk.strip()
        rules.append(
            Rule(
                rule_number=rule_number,
                section_title=_extract_section_title(chunk),
                rule_text=rule_text,
                full_text=rule_text,
            )
        )

    if skipped:
        logger.warning("Skipped %d chunks without rule numbers", skipped)
    logger.info("Parsed %d rules from rules file", len(rules))
    return rules
