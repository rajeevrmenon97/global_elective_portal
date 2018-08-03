#!/bin/bash

set -e

db="$1"
shift

while sleep 1; do
  if python -W ignore db-connect.py 2>&1 >/dev/null; then
    echo "Database is ready"
    break
  fi
  echo "Database is unavailable - sleeping"
done

cmd="$@" 
exec $cmd
