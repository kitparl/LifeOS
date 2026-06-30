#!/usr/bin/env bash
# Install or update AI-DLC workflow rules for Cursor from awslabs/aidlc-workflows releases.
# Usage: ./scripts/setup-aidlc.sh [version]
#   version: optional tag (default: latest), e.g. v1.0.0

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

VERSION="${1:-latest}"
cd "$ROOT"

if [[ "$VERSION" == "latest" ]]; then
  ASSET_URL="$(curl -sL -H "Accept: application/vnd.github+json" -H "User-Agent: LifeOS-setup" \
    "https://api.github.com/repos/awslabs/aidlc-workflows/releases/latest" \
    | python3 -c "import sys,json; r=json.load(sys.stdin); print(next(a['browser_download_url'] for a in r['assets'] if a['name'].endswith('.zip')))")"
else
  ASSET_URL="https://github.com/awslabs/aidlc-workflows/releases/download/${VERSION}/ai-dlc-rules-${VERSION}.zip"
fi

echo "Downloading AI-DLC rules from: $ASSET_URL"
curl -sL -o "$TMP_DIR/aidlc-rules.zip" "$ASSET_URL"
unzip -qo "$TMP_DIR/aidlc-rules.zip" -d "$TMP_DIR/extract"

rm -rf .aidlc/aidlc-rules
mkdir -p .aidlc .cursor/rules
cp -R "$TMP_DIR/extract/aidlc-rules" .aidlc/

ln -sfn .aidlc/aidlc-rules/aws-aidlc-rule-details .aidlc-rule-details

cat > .cursor/rules/ai-dlc-workflow.mdc << 'EOF'
---
description: "AI-DLC (AI-Driven Development Life Cycle) adaptive workflow for software development"
alwaysApply: true
---

When the user invokes AI-DLC (e.g., "Using AI-DLC, ..."), read and follow `.aidlc/aidlc-rules/aws-aidlc-rules/core-workflow.md` to start the workflow.
EOF

INSTALLED_VERSION="$(cat .aidlc/aidlc-rules/VERSION 2>/dev/null || echo unknown)"
echo "AI-DLC rules installed for Cursor: v${INSTALLED_VERSION}"
