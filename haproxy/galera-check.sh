#!/bin/sh
set -eu

HOST="${3:?Falta direccion del nodo}"
PORT="${4:?Falta puerto del nodo}"

export MYSQL_PWD="${GALERA_CHECK_PASSWORD:?Falta contrasena}"

ESTADO=$(timeout 4 mariadb \
  --protocol=TCP \
  --connect-timeout=2 \
  -h "$HOST" \
  -P "$PORT" \
  -u "${GALERA_CHECK_USER:?Falta usuario}" \
  -N -B -e "
    SHOW GLOBAL STATUS
    WHERE Variable_name IN (
      'wsrep_cluster_status',
      'wsrep_local_state_comment',
      'wsrep_ready'
    );
  ") || exit 1

printf '%s\n' "$ESTADO" | awk '
  $1 == "wsrep_cluster_status" && $2 == "Primary" { a=1 }
  $1 == "wsrep_local_state_comment" && $2 == "Synced" { b=1 }
  $1 == "wsrep_ready" && $2 == "ON" { c=1 }
  END { exit !(a && b && c) }
'
