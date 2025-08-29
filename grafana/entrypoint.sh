#!/bin/bash
if [ "$SSL_ENABLE" = "true" ]; then
    export GF_SERVER_ROOT_URL="https://${GRAFANA_HOST}:${GRAFANA_PORT}/"
else
    export GF_SERVER_ROOT_URL="http://${GRAFANA_HOST}:${GRAFANA_PORT}/"
fi

exec /run.sh "$@"
