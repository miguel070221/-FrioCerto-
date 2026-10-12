#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "=== 1. Containers ==="
docker compose ps
echo
echo "=== 2. Receber 14 mensagens MQTT (pode levar alguns segundos) ==="
docker compose exec -T mosquitto mosquitto_sub -h 127.0.0.1 -t 'friocerto/abc/+/+/+/leitura' -v -q 1 -C 14
echo
echo "=== 3. Últimas linhas do publisher ==="
tail -n 20 publisher.log || true
