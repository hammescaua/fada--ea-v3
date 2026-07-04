#!/usr/bin/env bash
# =============================================================================
# FADA — demonstração de 1 clique (Linux / macOS)
# Sobe a API + a web e abre o navegador já com o talhão de demonstração carregado.
# Uso:  ./scripts/demo-fada.sh      (feche com Ctrl+C — encerra tudo)
# Pré-requisito: o projeto já ter sido instalado uma vez
#   (apps/api/.venv criado e apps/web/node_modules instalado).
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")/.."          # raiz do repositório
ROOT="$(pwd)"
API_PORT=8000
WEB_PORT=3000
SEED_URL="http://localhost:${WEB_PORT}/fada-demo-seed.html"

echo "🌱 FADA — preparando a demonstração…"

# --- checagens de pré-requisito ---------------------------------------------
if [ ! -f "apps/api/.venv/bin/activate" ]; then
  echo "❌ Falta o ambiente da API (apps/api/.venv)."
  echo "   Rode uma vez:  cd apps/api && python3 -m venv .venv && . .venv/bin/activate && pip install -e ."
  exit 1
fi
if [ ! -d "apps/web/node_modules" ]; then
  echo "❌ Falta instalar a web (apps/web/node_modules)."
  echo "   Rode uma vez:  cd apps/web && npm install   (ou pnpm install)"
  exit 1
fi

# --- encerra tudo ao sair ----------------------------------------------------
API_PID=""; WEB_PID=""
cleanup() {
  echo ""; echo "⏹  Encerrando…"
  [ -n "$WEB_PID" ] && kill "$WEB_PID" 2>/dev/null || true
  [ -n "$API_PID" ] && kill "$API_PID" 2>/dev/null || true
  exit 0
}
trap cleanup INT TERM

# --- sobe a API --------------------------------------------------------------
echo "→ subindo a API (porta ${API_PORT})…"
( cd apps/api && . .venv/bin/activate && exec uvicorn app.main:app --port "${API_PORT}" ) \
  > "${ROOT}/.demo-api.log" 2>&1 &
API_PID=$!

# --- sobe a web --------------------------------------------------------------
echo "→ subindo a interface web (porta ${WEB_PORT})…"
( cd apps/web && exec npx next dev -p "${WEB_PORT}" ) \
  > "${ROOT}/.demo-web.log" 2>&1 &
WEB_PID=$!

# --- espera ficarem prontos --------------------------------------------------
echo -n "→ aguardando a API"
for i in $(seq 1 40); do
  if curl -sf "http://localhost:${API_PORT}/api/health" >/dev/null 2>&1; then echo " ✓"; break; fi
  echo -n "."; sleep 1
done
echo -n "→ aguardando a web"
for i in $(seq 1 60); do
  if curl -sf "http://localhost:${WEB_PORT}" >/dev/null 2>&1; then echo " ✓"; break; fi
  echo -n "."; sleep 1
done

# --- abre o navegador na página-semente (carrega os dados de demo) ----------
echo "→ abrindo o navegador com o talhão de demonstração…"
if command -v xdg-open >/dev/null 2>&1; then xdg-open "$SEED_URL" >/dev/null 2>&1 || true
elif command -v open      >/dev/null 2>&1; then open "$SEED_URL"      >/dev/null 2>&1 || true
else echo "   Abra manualmente:  $SEED_URL"; fi

echo ""
echo "✅ Pronto! A demonstração está no ar."
echo "   • App:   http://localhost:${WEB_PORT}"
echo "   • Recarregar dados de demo:  $SEED_URL"
echo "   • Logs:  .demo-api.log  /  .demo-web.log"
echo ""
echo "   (A primeira vez que abrir cada página leva alguns segundos para compilar.)"
echo "   Deixe esta janela aberta. Para encerrar tudo: Ctrl+C"
wait
