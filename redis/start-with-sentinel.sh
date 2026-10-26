#!/bin/sh
set -eu

SELF_IP="$(timeout 2 hostname -i 2>/dev/null | awk '{print $1}' || true)"
MASTER_HOST=""
MASTER_PORT="6379"

for SENTINEL in redis-sentinel1 redis-sentinel2 redis-sentinel3; do
  RESPUESTA="$(timeout 2 redis-cli --raw -h "$SENTINEL" -p 26379 \
    SENTINEL get-master-addr-by-name mymaster 2>/dev/null || true)"

  HOST="$(printf '%s\n' "$RESPUESTA" | sed -n '1p')"
  PORT="$(printf '%s\n' "$RESPUESTA" | sed -n '2p')"

  if [ -n "$HOST" ] && [ "$PORT" = "6379" ]; then
    MASTER_HOST="$HOST"
    MASTER_PORT="$PORT"
    break
  fi
done

if [ -z "$MASTER_HOST" ]; then
  if [ "${REDIS_OFFLINE_RECOVERY:-no}" != "yes" ]; then
    echo "Sentinel no disponible. Recuperacion offline no autorizada." >&2
    exit 1
  fi

  echo "Sentinel no disponible. Consultando configuraciones persistentes..."

  VOTOS_REDIS=0
  VOTOS_REPLICA=0

  for N in 1 2 3; do
    ARCHIVO="/sentinel-state/$N/sentinel.conf"

    if [ -s "$ARCHIVO" ]; then
      CANDIDATO="$(awk '$1=="sentinel" && $2=="monitor" && $3=="mymaster" && $5=="6379" {print $4; exit}' "$ARCHIVO")"

      case "$CANDIDATO" in
        redis)
          VOTOS_REDIS=$((VOTOS_REDIS + 1))
          ;;
        redis-replica)
          VOTOS_REPLICA=$((VOTOS_REPLICA + 1))
          ;;
      esac
    fi
  done

  if [ "$VOTOS_REDIS" -ge 2 ]; then
    MASTER_HOST="redis"
  elif [ "$VOTOS_REPLICA" -ge 2 ]; then
    MASTER_HOST="redis-replica"
  else
    echo "ERROR: No hay acuerdo suficiente para determinar el maestro." >&2
    exit 1
  fi

  echo "Maestro recuperado desde configuraciones: $MASTER_HOST"
fi

MASTER_IP="$(timeout 2 getent hosts "$MASTER_HOST" 2>/dev/null | awk 'NR==1 {print $1}' || true)"

echo "Nodo actual: $REDIS_SELF ($SELF_IP)"
echo "Maestro detectado: $MASTER_HOST ($MASTER_IP)"

if [ "$MASTER_HOST" = "$REDIS_SELF" ] ||
   [ "$MASTER_HOST" = "$SELF_IP" ] ||
   { [ -n "$MASTER_IP" ] && [ "$MASTER_IP" = "$SELF_IP" ]; }; then
  echo "Iniciando como MAESTRO"
  exec redis-server --appendonly yes --replica-announce-ip "$REDIS_SELF"
else
  echo "Iniciando como REPLICA"
  exec redis-server --appendonly yes --replicaof "$MASTER_HOST" "$MASTER_PORT" --replica-announce-ip "$REDIS_SELF"
fi
