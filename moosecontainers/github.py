"""Calls to the GitHub API and the GitHub container registry."""

import urllib.parse
from dataclasses import dataclass

import requests

from moosecontainers.config import (
    FULL_REPO,
    GITHUB_API_URL,
    ORG,
    REPO,
    URI_PREFIX,
)


def api_headers(github_token: str) -> dict:
    """Get the headers for authenticating to the GitHub API."""
    return {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def api_delete(url: str, token: str):
    """Call DELETE on the GitHub API."""
    response = requests.delete(
        f"{GITHUB_API_URL}{url}", headers=api_headers(token)
    )
    response.raise_for_status()


def api_get_paginated(url: str, token: str) -> list[dict]:
    """Call GET on the GitHub API with pagination."""
    url = f"{GITHUB_API_URL}{url}"
    result: list[dict] = []
    headers = api_headers(token)
    params: dict | None = {"per_page": 100}
    while url:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30,
        )
        response.raise_for_status()

        result.extend(response.json())

        url = response.links.get("next", {}).get("url")
        params = None

    return result


def get_pr_comment(pr: int, marker: str, github_token: str) -> int | None:
    """Find a previous comment from this job by looking for our marker."""
    url = f"{GITHUB_API_URL}repos/{FULL_REPO}/issues/{pr}/comments"

    while url:
        response = requests.get(url, headers=api_headers(github_token))
        response.raise_for_status()
        comments = response.json()

        for comment in comments:
            if marker in comment["body"]:
                id = comment["id"]
                assert isinstance(id, int)
                return id

        # Handle pagination
        url = response.links.get("next", {}).get("url")

    return None


def delete_pr_comment(comment_id: int, github_token: str):
    """Delete a GitHub comment by ID."""
    api_delete(f"repos/{FULL_REPO}/issues/comments/{comment_id}", github_token)
    print(f"Deleted previous comment {comment_id}")


def post_pr_comment(pr: int, body: str, marker: str, github_token: str):
    """Post a new comment to the PR, deleting the old one with the marker."""
    existing_id = get_pr_comment(pr, marker, github_token)

    if existing_id is not None:
        delete_pr_comment(existing_id, github_token)

    url = f"{GITHUB_API_URL}repos/{FULL_REPO}/issues/{pr}/comments"
    payload = {"body": f"{marker}\n{body}"}
    response = requests.post(
        url, json=payload, headers=api_headers(github_token)
    )
    response.raise_for_status()
    print(f"Posted comment: {response.json()['id']}")


def ghcr_token(github_token: str) -> str:
    """Get a GitHub GHCR token."""
    response = requests.get(
        "https://ghcr.io/token",
        params={
            "service": "ghcr.io",
            "scope": f"repository:{FULL_REPO}/moose-containers:pull",
        },
        auth=("token", github_token),
    )
    response.raise_for_status()
    return response.json()["token"]


def container_exists(repo: str, tag: str, ghcr_token: str) -> bool:
    """Check if the container with the given repo and tag exists on GitHub."""
    url = f"https://ghcr.io/v2/{FULL_REPO}/{repo}/manifests/{tag}"
    headers = {
        "Authorization": f"Bearer {ghcr_token}",
        "Accept": "application/vnd.oci.image.index.v1+json",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return True
    if (
        response.status_code == 404
        and (errors := response.json().get("errors")) is not None
        and len(errors) == 1
        and errors[0].get("code") == "MANIFEST_UNKNOWN"
    ):
        return False
    response.raise_for_status()
    return False


@dataclass
class GitHubContainer:
    """Data storage for a single container on GitHub."""

    name: str
    """Full name of the container."""
    id: int
    """GitHub ID for the container."""
    tags: list[str]
    """Tags for the container."""
    sha: str
    """The SHA for the container."""
    uri: str
    """URI for the container (sha256 definition, no tags)."""


class GitHubContainerRepoMissing(Exception):
    """Exception raised when a container repository is missing."""


def _package_versions_url(name: str) -> str:
    """Get the API url for the versions of the given container package."""
    quoted_name = urllib.parse.quote(name, safe="")
    return f"orgs/{ORG}/packages/container/{quoted_name}/versions"


def get_containers(repo: str, token: str) -> list[GitHubContainer]:
    """Get all of the containers under the given container repo."""
    name = f"{REPO}/{repo}"

    try:
        result = api_get_paginated(_package_versions_url(name), token)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise GitHubContainerRepoMissing from e
        raise

    return [
        GitHubContainer(
            name=name,
            id=v["id"],
            tags=v["metadata"]["container"]["tags"],
            sha=v["name"].split(":")[-1],
            uri=f"{URI_PREFIX}/{repo}@{v['name']}",
        )
        for v in result
    ]


def delete_container(github_container: GitHubContainer, token: str):
    """Delete a container from the GitHub container repository."""
    url = _package_versions_url(github_container.name)
    api_delete(f"{url}/{github_container.id}", token)
