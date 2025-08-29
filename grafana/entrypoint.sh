#!/bin/bash

# 根據 SSL_ENABLE 設置協議
if [ "$SSL_ENABLE" = "true" ]; then
    export GF_SERVER_ROOT_URL="https://${GRAFANA_HOST}:${GRAFANA_PORT}/"
else
    export GF_SERVER_ROOT_URL="http://${GRAFANA_HOST}:${GRAFANA_PORT}/"
fi

# 執行原始的 Grafana 命令
exec /run.sh "$@" 