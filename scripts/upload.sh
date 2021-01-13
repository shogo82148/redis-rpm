#!/bin/bash

set -uex

USER=shogo82148
DISTRO=$1
BINTRAY_API=https://api.bintray.com
SUBJECT=shogo82148
REPO=redis-rpm
ROOT=$(cd "$(dirname "$0")/../" && pwd)

SPEC_FILE="$ROOT/rpmbuild/SPECS/redis.spec"

VERSION=$(sed -ne 's/^Version:[[:space:]]*\([.0-9]*\).*/\1/p' "$SPEC_FILE")
RELEASE=$(sed -ne 's/^Release:[[:space:]]*\([.0-9]*\).*/\1/p' "$SPEC_FILE")

for PACKAGE in redis redis-debuginfo redis-devel redis-doc redis-trib
do
    : create a new version
    curl -u "$USER:$BINTRAY_API_KEY" \
        "$BINTRAY_API/packages/$SUBJECT/$REPO/$PACKAGE/versions" \
        -H 'Content-Type: application/json' \
        -d "$(
            jq -nc \
                --arg version "$VERSION-$RELEASE" \
                --arg desc "Automated release from main" \
                --arg released "$(date '+%Y-%m-%dT%H:%M:%S%z')" \
                '{ name: $version, released: $released }'
            )"

    : upload RPM files

    for RPM in "$ROOT/$DISTRO.build/$PACKAGE-$VERSION-$RELEASE".*.rpm
    do
        curl -u "$USER:$BINTRAY_API_KEY" \
            "$BINTRAY_API/content/$SUBJECT/$REPO/$DISTRO/2/x86_64/$(basename "$RPM")" \
            -H "X-Bintray-Package: $PACKAGE" \
            -H "X-Bintray-Version: $VERSION-$RELEASE" \
            -H "X-Bintray-Publish: 1" \
            -H "X-Bintray-Override: 1" \
            -H "Content-Type: application/octet-stream" \
            -XPUT \
            --data-binary "@$RPM"
    done
done
