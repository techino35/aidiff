"""Tests for the heuristic analyzer."""

from pathlib import Path

from aidiff.analyzer import FileAnalysis, LineScore, analyze_file


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestAnalyzeFile:
    """Tests for analyze_file function."""

    def test_sample_code_detected(self) -> None:
        """Sample AI-like code should have elevated AI score."""
        result = analyze_file(FIXTURES_DIR / "sample_code.py")
        assert isinstance(result, FileAnalysis)
        assert result.total_lines > 0
        assert result.ai_lines > 0
        assert result.ai_score > 0.1  # Should detect some AI patterns

    def test_explicit_tag_detected(self) -> None:
        """Explicit AI tags should score 1.0."""
        code = "x = 1  # ai-generated\ny = 2\n"
        result = analyze_file("test.py", content=code)
        tagged_lines = [ls for ls in result.line_scores if ls.score >= 1.0]
        assert len(tagged_lines) >= 1

    def test_placeholder_comment(self) -> None:
        """Placeholder TODO comments should be detected."""
        code = "# TODO: Add error handling for edge cases\nx = 1\n"
        result = analyze_file("test.py", content=code)
        assert result.line_scores[0].score >= 0.5

    def test_obvious_comment(self) -> None:
        """Obvious/redundant comments should be detected."""
        code = "# This is a helper function that processes data\ndef process(): pass\n"
        result = analyze_file("test.py", content=code)
        assert result.line_scores[0].score >= 0.4

    def test_verbose_variable(self) -> None:
        """Verbose variable names should be flagged."""
        code = "user_authentication_token_expiration_time = 123\n"
        result = analyze_file("test.py", content=code)
        assert result.line_scores[0].score >= 0.3

    def test_clean_human_code(self) -> None:
        """Simple human-like code should have low AI score."""
        code = "x = 1\ny = x + 2\nprint(y)\n"
        result = analyze_file("test.py", content=code)
        assert result.ai_score < 0.2

    def test_empty_file(self) -> None:
        """Empty file should return zero scores."""
        result = analyze_file("test.py", content="")
        assert result.total_lines == 0
        assert result.ai_score == 0.0

    def test_nonexistent_file(self) -> None:
        """Nonexistent file should return empty result."""
        result = analyze_file("/nonexistent/file.py")
        assert result.total_lines == 0
        assert result.ai_score == 0.0
