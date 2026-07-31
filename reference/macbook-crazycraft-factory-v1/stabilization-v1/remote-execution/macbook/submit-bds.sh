#!/bin/sh
set -eu
role="$1"
config="$2"
bundle="$3"
case "$role" in T1|T10) ;; *) echo "role must be T1 or T10" >&2; exit 2;; esac
exec python3 "$(dirname "$0")/remote_jobs.py" submit --role "$role" --transport ssh --wait --config "$config" --bundle "$bundle"
