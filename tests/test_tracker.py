"""Tests for the tracker module."""

import re
from unittest.mock import MagicMock

from aidiff.tracker import (
    COMMIT_AI_PATTERNS,
    CommitInfo,
    classify_commit,
)


class TestCommitPatterns:
    """Tests for commit message AI pattern detection."""

    def test_ai_tag_detected(self) -> None:
        """[AI] tag in commit message should match."""
        assert any(p.search("[AI] fix login bug") for p in COMMIT_AI_PATTERNS)

    def test_claude_tag_detected(self) -> None:
        """[Claude] tag should match."""
        assert any(p.search("[Claude] refactor auth") for p in COMMIT_AI_PATTERNS)

    def test_copilot_tag_detected(self) -> None:
        """[Copilot] tag should match."""
        assert any(p.search("[Copilot] add tests") for p in COMMIT_AI_PATTERNS)

    def test_coauthored_detected(self) -> None:
        """Co-authored-by with AI name should match."""
        msg = "fix: login\n\nCo-authored-by: Claude <noreply@anthropic.com>"
        assert any(p.search(msg) for p in COMMIT_AI_PATTERNS)

    def test_normal_commit_not_detected(self) -> None:
        """Regular commit message should not match."""
        msg = "fix: resolve login timeout issue"
        assert not any(p.search(msg) for p in COMMIT_AI_PATTERNS)

    def test_cursor_detected(self) -> None:
        """Cursor mention should match."""
        assert any(p.search("implemented with cursor") for p in COMMIT_AI_PATTERNS)


class TestClassifyCommit:
    """Tests for classify_commit function."""

    def _make_commit(self, message: str, author: str = "Developer") -> MagicMock:
        """Create a mock commit object."""
        commit = MagicMock()
        commit.message = message
        commit.author.name = author
        commit.hexsha = "abc12345" * 5
        commit.committed_date = 1700000000
        return commit

    def test_ai_commit(self) -> None:
        """Commit with AI tag should be classified as AI."""
        commit = self._make_commit("[AI] add feature")
        info = classify_commit(commit)
        assert info.is_ai_commit
        assert len(info.ai_indicators) > 0

    def test_human_commit(self) -> None:
        """Normal commit should not be classified as AI."""
        commit = self._make_commit("fix: resolve timeout")
        info = classify_commit(commit)
        assert not info.is_ai_commit

    def test_co_authored_commit(self) -> None:
        """Co-authored-by Claude should be detected."""
        msg = "feat: add auth\n\nCo-authored-by: Claude <noreply@anthropic.com>"
        commit = self._make_commit(msg)
        info = classify_commit(commit)
        assert info.is_ai_commit
