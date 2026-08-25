#!/bin/bash
# Script wrapper para Claude Desktop no Windows com WSL.
# Carrega credenciais do ~/.config/omie-mcp/.env e executa o servidor MCP.
set -euo pipefail

ENV_FILE="$HOME/.config/omie-mcp/.env"

# Commit revisado deste fork. Trave numa revisão que você leu: um ref sem pin
# (uvx --from git+https://.../omie-mcp) resolve o HEAD a cada execução, e
# qualquer push futuro passa a rodar como código local com as suas credenciais
# do OMIE no ambiente. Atualize este SHA de propósito, revisando o diff.
OMIE_MCP_REF="${OMIE_MCP_REF:-}"

if [ -z "$OMIE_MCP_REF" ]; then
  echo "run.sh: defina OMIE_MCP_REF com o commit revisado (ex: OMIE_MCP_REF=abc1234)." >&2
  echo "         Rodar sem pin executaria o HEAD do repositório remoto." >&2
  exit 1
fi

if [ -f "$ENV_FILE" ]; then
  # As credenciais não deveriam estar legíveis por outros usuários da máquina.
  PERM=$(stat -c '%a' "$ENV_FILE" 2>/dev/null || stat -f '%OLp' "$ENV_FILE")
  if [ "$PERM" != "600" ]; then
    echo "run.sh: $ENV_FILE está com permissão $PERM; corrigindo para 600." >&2
    chmod 600 "$ENV_FILE"
  fi
  set -o allexport
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +o allexport
fi

exec uvx --from "git+https://github.com/cloudpark/omie-mcp@${OMIE_MCP_REF}" omie-mcp
