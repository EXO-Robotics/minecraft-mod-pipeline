#!/bin/sh
set -eu
exec python3 "$(dirname "$0")/remote_jobs.py" retrieve --role "$1" --transport ssh --config "$2" --job-id "$3" --destination "$4"
