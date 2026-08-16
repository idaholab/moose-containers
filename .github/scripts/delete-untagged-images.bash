#!/bin/bash
set -euo pipefail

ORG=idaholab
REPO=moose-containers

echo "Getting container packages for $ORG..."
gh api \
    --paginate \
    "/orgs/$ORG/packages?package_type=container&per_page=100" \
    --jq '.[].name' |
while IFS= read -r package; do
    if [[ "$package" != ${REPO}/* ]]; then
        continue
    fi
    echo "Checking package: $package"

    # URL-encode the package name because GHCR package names may contain /
    encoded_package="$(jq -rn --arg x "$package" '$x|@uri')"

    gh api \
        --paginate \
        "/orgs/$ORG/packages/container/$encoded_package/versions?per_page=100" \
        --jq '.[] | select(.metadata.container.tags | length == 0) | .id' |
    while IFS= read -r version_id; do
        echo "Deleting untagged version $version_id from $package"

        gh api \
            --method DELETE \
            "/orgs/$ORG/packages/container/$encoded_package/versions/$version_id"
    done
done
