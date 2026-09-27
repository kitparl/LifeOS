#!/bin/sh
# Never run the sandbox API without a token (SECURITY-09).
if [ -z "$ES_AUTH_TOKEN" ]; then
  echo "ES_AUTH_TOKEN is required (set DSA_JUDGE_TOKEN for docker compose)" >&2
  exit 1
fi
exec /opt/go-judge -mount-conf /opt/mount.yaml "$@"
