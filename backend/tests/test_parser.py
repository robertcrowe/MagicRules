import re

import pytest

from backend.models import Rule
from backend.parser import RULE_NUMBER_PATTERN, parse_rules_file

RULE_RE = re.compile(r"^\d+\.\d+[a-z]?$")


@pytest.mark.integration
def test_parse_rules_file_returns_non_empty_list():
    rules = parse_rules_file()
    assert len(rules) > 0, "parse_rules_file() should return at least one rule"


@pytest.mark.integration
def test_each_rule_has_valid_rule_number():
    rules = parse_rules_file()
    for rule in rules:
        assert rule.rule_number, f"rule_number must not be empty: {rule}"
        assert RULE_RE.match(rule.rule_number), (
            f"rule_number '{rule.rule_number}' does not match expected pattern"
        )


@pytest.mark.integration
def test_each_rule_has_non_empty_rule_text():
    rules = parse_rules_file()
    for rule in rules:
        assert rule.rule_text.strip(), f"rule_text must not be empty for rule {rule.rule_number}"


@pytest.mark.integration
def test_rule_numbers_are_unique():
    rules = parse_rules_file()
    numbers = [r.rule_number for r in rules]
    assert len(numbers) == len(set(numbers)), "Duplicate rule_numbers found"


def test_rule_model_fields():
    rule = Rule(rule_number="100.1", section_title="Test", rule_text="Text", full_text="Full")
    assert rule.rule_number == "100.1"
    assert rule.section_title == "Test"
    assert rule.embedding is None


def test_rule_number_pattern_matches_valid():
    valid = ["100.1", "603.3a", "107.3k", "800.4b"]
    for n in valid:
        assert RULE_NUMBER_PATTERN.search(n), f"Pattern should match '{n}'"


def test_rule_number_pattern_rejects_invalid():
    invalid = ["abc", "100", "rule 100.1", ""]
    for n in invalid:
        assert not RULE_NUMBER_PATTERN.match(n), f"Pattern should not match '{n}'"
