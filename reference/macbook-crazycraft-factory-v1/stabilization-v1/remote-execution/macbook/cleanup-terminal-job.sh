#!/bin/sh
set -eu
exec python3 "$(dirname "$0")/remote_jobs.py" cleanup --role "$1" --transport ssh --config "$2" --job-id "$3"
