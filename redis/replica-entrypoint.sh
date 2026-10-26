#!/bin/sh
set -eu

SENTINEL_HOST="${SENTINEL_HOST:-redis-sentinel1}"
SENTINEL_PORT="${SENTINEL_PORT:-26379}"
MASTER_NAME="${MASTER_NAME:-mymaster}"

echo "Consultando el maestro actual a Sentinel..."

MASTER_INFO="$(redis-cli -h "$SENTINEL_HOST" -p "$SENTINEL_PORT" SENTINEL get-master-addr-by-name "$MASTER_NAME")"

MASTER_IP="$(printf '%s\n' "$MASTER_INFO" | sed -n '1p')"
MASTER_PORT="$(printf '%s\n' "$MASTER_INFO" | sed -n '2p')"

if [ -z "$MASTER_IP" ] || [ -z "$MASTER_PORT" ]; then
  echo "ERROR: Sentinel no devolvió una dirección de maestro."
  exit 1
fi

echo "Configurando réplica hacia ${MASTER_IP}:${MASTER_PORT}"

exec redis-server --replicaof "$MASTER_IP" "$MASTER_PORT"