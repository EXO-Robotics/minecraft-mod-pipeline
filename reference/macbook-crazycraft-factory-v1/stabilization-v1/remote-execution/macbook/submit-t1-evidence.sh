#!/bin/sh
set -eu
exec python3 "$(dirname "$0")/remote_jobs.py" submit --role T1 --transport ssh --wait --config "$1" --bundle "$2"
