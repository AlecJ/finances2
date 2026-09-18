#!/bin/sh
set -e

case "$1" in
  process)
    cd src && exec python3 main.py
    ;;
  test)
    exec python3 -m pytest
    ;;
  shell)
    exec bash
    ;;
  *)
    exec "$@"
    ;;
esac
