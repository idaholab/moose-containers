"""Tests for moosecontainers.actions.prepare_pr."""

from moosecontainers.actions.prepare_pr import MARKER
from moosecontainers.cli import main, parse_args
from moosecontainers.config import GITHUB_API_URL

COMMENTS_URL = (
    f"{GITHUB_API_URL}repos/idaholab/moose-containers/issues/5/comments"
)
"""The comments url for pull request 5."""


def test_parser():
    """Parse the arguments."""
    args = parse_args(["prepare_pr", "5", "main", "--github-token", "t"])
    assert (args.pr, args.base_ref, args.github_token) == (5, "main", "t")


def test_run(repo, capsys):
    """Run without a token; no comment is posted."""
    main(["prepare_pr", "5", "HEAD"])
    assert "No containers to build" in capsys.readouterr().out


def test_run_no_github_action(repo, registry, mock_requests):
    """Run with a token outside of a GitHub action; no comment is posted."""
    main(["prepare_pr", "5", "HEAD", "--github-token", "t"])
    assert not any(
        c.request.url.startswith(COMMENTS_URL) for c in mock_requests.calls
    )


def test_run_comment(repo, registry, mock_requests, github_action, capsys):
    """Run with a token in a GitHub action; a comment is posted."""
    mock_requests.get(COMMENTS_URL, json=[])
    post = mock_requests.post(COMMENTS_URL, json={"id": 1})
    main(["prepare_pr", "5", "HEAD", "--github-token", "t"])

    body = post.calls[0].request.body.decode()
    assert body.startswith('{"body": "' + MARKER)
    assert "No containers to build" in body
    out = capsys.readouterr().out
    assert "::group::Post pull request comment\nPosted comment: 1\n" in out
