from app.llm.response_parser import ResponseParser


def test_clean_returns_empty_for_none_or_empty_string() -> None:
    """Verify clean returns an empty string for None or blank input."""
    assert ResponseParser.clean(None) == ""
    assert ResponseParser.clean("") == ""


def test_clean_removes_think_blocks_and_collapses_blank_lines() -> None:
    """Verify <think> blocks are removed and blank lines collapse."""
    raw = (
        "Hello\n"
        "<think>internal reasoning</think>\n"
        "World\n\n\n"
        "<think>another thought</think>\n"
        "Bye\n"
    )

    cleaned = ResponseParser.clean(raw)

    assert "<think>" not in cleaned
    assert "internal reasoning" not in cleaned
    assert cleaned == "Hello\n\nWorld\n\nBye"


def test_clean_trims_whitespace_and_preserves_text() -> None:
    """Verify whitespace is trimmed while preserving actual model response."""
    raw = "  Leading and trailing text  \n"
    assert ResponseParser.clean(raw) == "Leading and trailing text"


def test_clean_preserves_non_think_brackets() -> None:
    """Verify only <think> blocks are removed, and other markup remains."""
    raw = "Start <note>keep this</note> end"

    assert ResponseParser.clean(raw) == "Start <note>keep this</note> end"
