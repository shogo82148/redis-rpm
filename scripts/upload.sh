#!/bin/bash

set -uex

USER=shogo82148
DISTRO=$1
BINTRAY_API=https://api.bintray.com
SUBJECT=shogo82148
REPO=redis-rpm
ROOT=$(cd "$(dirname "$0")/../" && pwd)

SPEC_FILE="$ROOT/rpmbuild/SPECS/redis.spec"

DATE=$(date '+%Y-%m-%dT%H:%M:%S%z')
VERSION=$(sed -ne 's/^Version:[[:space:]]*\([.0-9]*\).*/\1/p' "$SPEC_FILE")
RELEASE=$(sed -ne 's/^Release:[[:space:]]*\([.0-9]*\).*/\1/p' "$SPEC_FILE")

function upload () {
    PACKAGE=$1
    RPM=$2
    UPLOAD_PATH=$3
    if [[ -f "$RPM" ]]; then
        curl -u "$USER:$BINTRAY_API_KEY" \
            "$BINTRAY_API/packages/$SUBJECT/$REPO/$PACKAGE/versions" \
            -H 'Content-Type: application/json' \
            -d "$(
                jq -nc \
                    --arg version "$VERSION-$RELEASE" \
                    --arg desc "Automated release from main" \
                    --arg released "$DATE" \
                    '{ name: $version, released: $released }'
                )"
        curl -u "$USER:$BINTRAY_API_KEY" \
            "$BINTRAY_API/content/$SUBJECT/$REPO/$UPLOAD_PATH/$(basename "$RPM")" \
            -H "X-Bintray-Package: $PACKAGE" \
            -H "X-Bintray-Version: $VERSION-$RELEASE" \
            -H "X-Bintray-Publish: 1" \
            -H "X-Bintray-Override: 1" \
            -H "Content-Type: application/octet-stream" \
            -XPUT \
            --data-binary "@$RPM"
    fi
}

if [[ "$DISTRO" = "amazonlinux2" ]]; then
    upload redis "$ROOT/amazonlinux2.build/RPMS/x86_64/redis-$VERSION-$RELEASE.amzn2.x86_64.rpm" "amazonlinux2/2/x86_64"
    upload redis-debuginfo "$ROOT/amazonlinux2.build/RPMS/x86_64/redis-debuginfo-$VERSION-$RELEASE.amzn2.x86_64.rpm" "amazonlinux2/2/x86_64"
    upload redis-devel "$ROOT/amazonlinux2.build/RPMS/x86_64/redis-devel-$VERSION-$RELEASE.amzn2.x86_64.rpm" "amazonlinux2/2/x86_64"
    upload redis-doc "$ROOT/amazonlinux2.build/RPMS/noarch/redis-doc-$VERSION-$RELEASE.amzn2.x86_64.rpm" "amazonlinux2/2/noarch"
    upload redis-trib "$ROOT/amazonlinux2.build/RPMS/noarch/redis-trib-$VERSION-$RELEASE.amzn2.x86_64.rpm" "amazonlinux2/2/noarch"
fi

if [[ "$DISTRO" = "centos7" ]]; then
    upload redis "$ROOT/centos7.build/RPMS/x86_64/redis-$VERSION-$RELEASE.amzn2.x86_64.rpm" "centos/7/x86_64"
    upload redis-debuginfo "$ROOT/centos7.build/RPMS/x86_64/redis-debuginfo-$VERSION-$RELEASE.amzn2.x86_64.rpm" "centos/7/x86_64"
    upload redis-devel "$ROOT/centos7.build/RPMS/x86_64/redis-devel-$VERSION-$RELEASE.amzn2.x86_64.rpm" "centos/7/x86_64"
    upload redis-doc "$ROOT/centos7.build/RPMS/noarch/redis-doc-$VERSION-$RELEASE.amzn2.x86_64.rpm" "centos/7/noarch"
    upload redis-trib "$ROOT/centos7.build/RPMS/noarch/redis-trib-$VERSION-$RELEASE.amzn2.x86_64.rpm" "centos/7/noarch"
fi
