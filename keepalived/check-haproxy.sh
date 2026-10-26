#!/bin/sh

PORT="${1:-}"

case "$PORT" in
  80)
    RUTA="/"
    ;;
  8080)
    RUTA="/products/cheapest"
    ;;
  *)
    echo "Puerto no reconocido: $PORT" >&2
    exit 2
    ;;
esac

exec wget -q -T 2 -t 1 -O /dev/null   "http://127.0.0.1:${PORT}${RUTA}"
