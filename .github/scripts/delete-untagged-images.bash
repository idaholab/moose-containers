#!/bin/bash
set -euo pipefail

ORG=idaholab
REPO=moose-containers

gh api \
    --paginate \
    "/orgs/$ORG/packages?package_type=container&per_page=100" \
    --jq '.[] | [.name, .url] | @tsv' |
while IFS=$'\t' read -r package package_url; do
    if [[ "$package" != ${REPO}/* ]]; then
        continue
    fi
    echo "Checking package: $package"

    gh api \
        --paginate \
        "$package_url/versions?per_page=100" \
        --jq '.[] |
            select(.metadata.container.tags | length == 0) |
            .id' |
    while IFS= read -r version_id; do
        echo "Deleting: $package version=$version_id"

        gh api \
            --method DELETE \
            "$package_url/versions/$version_id"
    done
done
