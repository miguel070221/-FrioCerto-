#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -f .env ]]; then
  echo "Arquivo .env já existe; não foi substituído."
else
  umask 077
  cat > .env <<EOF
INFLUX_USER=admin
INFLUX_PASSWORD=$(openssl rand -hex 18)
INFLUX_TOKEN=$(openssl rand -hex 32)
GRAFANA_PASSWORD=$(openssl rand -hex 18)
EOF
  echo "Credenciais locais criadas em .env (arquivo ignorado pelo Git)."
fi
echo "Execute: docker compose up -d"
