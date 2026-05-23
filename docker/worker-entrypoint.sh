#!/usr/bin/env bash

set -euo pipefail

mkdir -p /app/static/uploads
chown -R appuser:appuser /app/static/uploads

exec gosu appuser "$@"
