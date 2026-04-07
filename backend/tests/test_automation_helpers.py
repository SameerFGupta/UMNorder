import pytest
from backend.automation import normalize_text

def test_normalize_text():
    # Edge case: None
    assert normalize_text(None) == ""

    # Edge case: Empty string
    assert normalize_text("") == ""

    # Edge case: Whitespace only
    assert normalize_text("   ") == ""
    assert normalize_text("\t\n") == ""

    # Edge case: Leading/trailing whitespace
    assert normalize_text(" a ") == "a"
    assert normalize_text(" a b c ") == "a b c"

    # Edge case: Multiple spaces
    assert normalize_text("a  b") == "a b"
    assert normalize_text("a   b") == "a  b"  # Note: replace("  ", " ") is only called once, so "   " becomes "  "

    # Edge case: Hyphens
    assert normalize_text("a-b") == "ab"
    assert normalize_text("-a-b-") == "ab"
    assert normalize_text("a--b") == "ab"

    # Edge case: Lowercasing
    assert normalize_text("ABC") == "abc"
    assert normalize_text("A-b  C") == "ab c"

    # Edge case: Combinations
    assert normalize_text("  A-B  C-D  ") == "ab cd"
