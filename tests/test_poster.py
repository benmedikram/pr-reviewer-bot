from unittest.mock import MagicMock, patch
from reviewer.poster import post_review

FINDINGS = [
    {"file": "a.py", "line": 2, "severity": "high", "message": "bug", "confidence": 0.9},
]


def test_review_type_is_hardcoded_to_comment():
    with patch("reviewer.poster.get_installation_token", return_value="tok"), \
         patch("reviewer.poster.Github") as MockGithub:
        mock_pr = MagicMock()
        MockGithub.return_value.get_repo.return_value.get_pull.return_value = mock_pr

        post_review(123, "user/repo", 1, FINDINGS, dry_run=False)

        _, kwargs = mock_pr.create_review.call_args
        assert kwargs["event"] == "COMMENT"


def test_review_posts_one_comment_per_finding():
    with patch("reviewer.poster.get_installation_token", return_value="tok"), \
         patch("reviewer.poster.Github") as MockGithub:
        mock_pr = MagicMock()
        MockGithub.return_value.get_repo.return_value.get_pull.return_value = mock_pr

        post_review(123, "user/repo", 1, FINDINGS, dry_run=False)

        _, kwargs = mock_pr.create_review.call_args
        assert kwargs["comments"] == [
            {"path": "a.py", "line": 2, "body": "**HIGH** (confidence 0.90): bug"}
        ]


def test_no_findings_posts_nothing():
    with patch("reviewer.poster.get_installation_token", return_value="tok"), \
         patch("reviewer.poster.Github") as MockGithub:
        mock_pr = MagicMock()
        MockGithub.return_value.get_repo.return_value.get_pull.return_value = mock_pr

        result = post_review(123, "user/repo", 1, [], dry_run=False)

        assert result is None
        mock_pr.create_review.assert_not_called()


def test_dry_run_posts_nothing_and_prints(capsys):
    with patch("reviewer.poster.Github") as MockGithub:
        result = post_review(123, "user/repo", 1, FINDINGS, dry_run=True)

        assert result is None
        MockGithub.assert_not_called()  # dry-run never touches the GitHub API
        captured = capsys.readouterr()
        assert "a.py" in captured.out