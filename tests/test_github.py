"""Tests for moosecontainers.github."""

import pytest
import requests
import responses

from moosecontainers import github
from moosecontainers.config import GITHUB_API_URL, URI_PREFIX

TOKEN = "token"
"""The github token used in the tests."""

COMMENTS_URL = (
    f"{GITHUB_API_URL}repos/idaholab/moose-containers/issues/5/comments"
)
"""The comments url for pull request 5."""

VERSIONS_URL = (
    f"{GITHUB_API_URL}orgs/idaholab/packages/container/"
    "moose-containers%2Ffoo/versions"
)
"""The package versions url for the foo container repo."""


def test_api_headers():
    """The API headers include the token."""
    headers = github.api_headers(TOKEN)
    assert headers["Authorization"] == f"Bearer {TOKEN}"


def test_api_delete(mock_requests):
    """Call DELETE on the API."""
    mock_requests.delete(f"{GITHUB_API_URL}foo", status=204)
    github.api_delete("foo", TOKEN)
    request = mock_requests.calls[0].request
    assert request.headers["Authorization"] == f"Bearer {TOKEN}"


def test_api_delete_error(mock_requests):
    """An error from DELETE raises."""
    mock_requests.delete(f"{GITHUB_API_URL}foo", status=500)
    with pytest.raises(requests.exceptions.HTTPError):
        github.api_delete("foo", TOKEN)


def test_api_get_paginated(mock_requests):
    """Call GET on the API and follow pagination."""
    next_url = f"{GITHUB_API_URL}foo?page=2"
    mock_requests.get(
        f"{GITHUB_API_URL}foo",
        json=[1, 2],
        headers={"Link": f'<{next_url}>; rel="next"'},
        match=[responses.matchers.query_param_matcher({"per_page": "100"})],
    )
    mock_requests.get(next_url, json=[3])
    assert github.api_get_paginated("foo", TOKEN) == [1, 2, 3]


def test_api_get_paginated_error(mock_requests):
    """An error from GET raises."""
    mock_requests.get(f"{GITHUB_API_URL}foo", status=404)
    with pytest.raises(requests.exceptions.HTTPError):
        github.api_get_paginated("foo", TOKEN)


def test_get_pr_comment(mock_requests):
    """Find a comment with the marker, following pagination."""
    next_url = f"{COMMENTS_URL}?page=2"
    mock_requests.get(
        COMMENTS_URL,
        json=[{"id": 1, "body": "other"}],
        headers={"Link": f'<{next_url}>; rel="next"'},
    )
    mock_requests.get(next_url, json=[{"id": 2, "body": "a <!-- m --> b"}])
    assert github.get_pr_comment(5, "<!-- m -->", TOKEN) == 2


def test_get_pr_comment_missing(mock_requests):
    """No comment with the marker."""
    mock_requests.get(COMMENTS_URL, json=[{"id": 1, "body": "other"}])
    assert github.get_pr_comment(5, "<!-- m -->", TOKEN) is None


def test_get_pr_comment_error(mock_requests):
    """An error when getting comments raises."""
    mock_requests.get(COMMENTS_URL, status=403)
    with pytest.raises(requests.exceptions.HTTPError):
        github.get_pr_comment(5, "<!-- m -->", TOKEN)


def test_delete_pr_comment(mock_requests, capsys):
    """Delete a comment."""
    mock_requests.delete(
        f"{GITHUB_API_URL}repos/idaholab/moose-containers/issues/comments/3"
    )
    github.delete_pr_comment(3, TOKEN)
    assert capsys.readouterr().out == "Deleted previous comment 3\n"


@pytest.mark.parametrize("existing", [True, False])
def test_post_pr_comment(mock_requests, capsys, existing):
    """Post a comment, deleting the previous one if it exists."""
    comments = [{"id": 3, "body": "<!-- m -->\nold"}] if existing else []
    mock_requests.get(COMMENTS_URL, json=comments)
    delete = mock_requests.delete(
        f"{GITHUB_API_URL}repos/idaholab/moose-containers/issues/comments/3"
    )
    post = mock_requests.post(
        COMMENTS_URL,
        json={"id": 4},
        match=[
            responses.matchers.json_params_matcher({"body": "<!-- m -->\nhi"})
        ],
    )
    github.post_pr_comment(5, "hi", "<!-- m -->", TOKEN)
    assert delete.call_count == (1 if existing else 0)
    assert post.call_count == 1
    assert capsys.readouterr().out.endswith("Posted comment: 4\n")


def test_post_pr_comment_error(mock_requests):
    """An error when posting a comment raises."""
    mock_requests.get(COMMENTS_URL, json=[])
    mock_requests.post(COMMENTS_URL, status=500)
    with pytest.raises(requests.exceptions.HTTPError):
        github.post_pr_comment(5, "hi", "<!-- m -->", TOKEN)


def test_ghcr_token(mock_requests):
    """Get a GHCR token."""
    mock_requests.get(
        "https://ghcr.io/token",
        json={"token": "ghcr"},
        match=[
            responses.matchers.query_param_matcher(
                {
                    "service": "ghcr.io",
                    "scope": "repository:idaholab/moose-containers/"
                    "moose-containers:pull",
                }
            )
        ],
    )
    assert github.ghcr_token(TOKEN) == "ghcr"


def test_ghcr_token_error(mock_requests):
    """An error when getting a GHCR token raises."""
    mock_requests.get("https://ghcr.io/token", status=401)
    with pytest.raises(requests.exceptions.HTTPError):
        github.ghcr_token(TOKEN)


MANIFEST_URL = "https://ghcr.io/v2/idaholab/moose-containers/foo/manifests/bar"
"""The manifest url for foo:bar."""


def test_container_exists(mock_requests):
    """A container that exists."""
    mock_requests.get(MANIFEST_URL, status=200)
    assert github.container_exists("foo", "bar", "ghcr")
    request = mock_requests.calls[0].request
    assert request.headers["Authorization"] == "Bearer ghcr"


def test_container_exists_missing(mock_requests):
    """A container that does not exist."""
    mock_requests.get(
        MANIFEST_URL,
        status=404,
        json={"errors": [{"code": "MANIFEST_UNKNOWN"}]},
    )
    assert not github.container_exists("foo", "bar", "ghcr")


@pytest.mark.parametrize(
    "json",
    [
        {},
        {"errors": []},
        {"errors": [{"code": "NAME_UNKNOWN"}]},
        {
            "errors": [
                {"code": "MANIFEST_UNKNOWN"},
                {"code": "MANIFEST_UNKNOWN"},
            ]
        },
    ],
)
def test_container_exists_other_404(mock_requests, json):
    """Any other 404 raises."""
    mock_requests.get(MANIFEST_URL, status=404, json=json)
    with pytest.raises(requests.exceptions.HTTPError):
        github.container_exists("foo", "bar", "ghcr")


def test_container_exists_other_status(mock_requests):
    """A status that is not an error or found is treated as not existing."""
    mock_requests.get(MANIFEST_URL, status=204)
    assert not github.container_exists("foo", "bar", "ghcr")


def test_container_exists_error(mock_requests):
    """A server error raises."""
    mock_requests.get(MANIFEST_URL, status=500)
    with pytest.raises(requests.exceptions.HTTPError):
        github.container_exists("foo", "bar", "ghcr")


def test_get_containers(mock_requests):
    """Get the containers in a container repo."""
    mock_requests.get(
        VERSIONS_URL,
        json=[
            {
                "id": 1,
                "name": "sha256:abc",
                "metadata": {"container": {"tags": ["t"]}},
            }
        ],
    )
    assert github.get_containers("foo", TOKEN) == [
        github.GitHubContainer(
            name="moose-containers/foo",
            id=1,
            tags=["t"],
            sha="abc",
            uri=f"{URI_PREFIX}/foo@sha256:abc",
        )
    ]


def test_get_containers_missing(mock_requests):
    """A missing container repo raises GitHubContainerRepoMissing."""
    mock_requests.get(VERSIONS_URL, status=404)
    with pytest.raises(github.GitHubContainerRepoMissing):
        github.get_containers("foo", TOKEN)


def test_get_containers_error(mock_requests):
    """Any other error raises."""
    mock_requests.get(VERSIONS_URL, status=500)
    with pytest.raises(requests.exceptions.HTTPError):
        github.get_containers("foo", TOKEN)


def test_delete_container(mock_requests):
    """Delete a container."""
    delete = mock_requests.delete(f"{VERSIONS_URL}/1", status=204)
    container = github.GitHubContainer(
        name="moose-containers/foo", id=1, tags=[], sha="abc", uri=""
    )
    github.delete_container(container, TOKEN)
    assert delete.call_count == 1
