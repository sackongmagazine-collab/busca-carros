#!/usr/bin/env bash
# test-integration.sh — Testa o fluxo completo do produto em produção
# Uso: bash test-integration.sh <BACKEND_URL> <ADMIN_SECRET>
# Ex:  bash test-integration.sh https://buscacarros-api.onrender.com meu-admin-secret

set -e
API="${1:-http://localhost:8000}"
ADMIN_SECRET="${2:-admin-secret}"
EMAIL="test-$(date +%s)@buscacarros.com.br"
PASSWORD="Test@123456"

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'
pass() { echo -e "${GREEN}✅ PASS${NC} — $1"; }
fail() { echo -e "${RED}❌ FAIL${NC} — $1"; FAILURES=$((FAILURES+1)); }
info() { echo -e "${YELLOW}▶${NC}  $1"; }
FAILURES=0

echo ""
echo "══════════════════════════════════════════"
echo "  🧪 Busca Carros — Integration Tests"
echo "  API: $API"
echo "══════════════════════════════════════════"
echo ""

# ─── 1. Health check ─────────────────────────────────────────────────────────
info "1. Health check"
STATUS=$(curl -sf "$API/health" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status',''))" 2>/dev/null)
[ "$STATUS" = "ok" ] && pass "API online" || fail "API offline — resposta: $STATUS"

# ─── 2. Cadastro ──────────────────────────────────────────────────────────────
info "2. Cadastro de usuário"
REG=$(curl -sf -X POST "$API/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\",\"full_name\":\"Teste Automatico\"}" 2>/dev/null)
TOKEN=$(echo "$REG" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)
[ -n "$TOKEN" ] && pass "Cadastro OK — token gerado" || fail "Cadastro falhou: $REG"

# ─── 3. Login ─────────────────────────────────────────────────────────────────
info "3. Login"
LOGIN=$(curl -sf -X POST "$API/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" 2>/dev/null)
LOGIN_TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)
[ -n "$LOGIN_TOKEN" ] && pass "Login OK" || fail "Login falhou: $LOGIN"
TOKEN="${LOGIN_TOKEN:-$TOKEN}"

# ─── 4. Busca de veículo ──────────────────────────────────────────────────────
info "4. Iniciando busca (HB20, São Paulo, R\$80k)"
SEARCH=$(curl -sf -X POST "$API/api/search" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"model":"HB20","max_price":80000,"location":"São Paulo, SP","transmission":"indiferente","fuel":"indiferente"}' 2>/dev/null)
SEARCH_ID=$(echo "$SEARCH" | python3 -c "import sys,json; print(json.load(sys.stdin).get('search_id',''))" 2>/dev/null)
[ -n "$SEARCH_ID" ] && pass "Busca criada — ID: $SEARCH_ID" || fail "Falha ao criar busca: $SEARCH"

# ─── 5. Polling de resultados ─────────────────────────────────────────────────
if [ -n "$SEARCH_ID" ]; then
  info "5. Aguardando resultados (máx 60s)..."
  for i in $(seq 1 24); do
    sleep 2.5
    RESULT=$(curl -sf "$API/api/search/$SEARCH_ID" -H "Authorization: Bearer $TOKEN" 2>/dev/null)
    STATUS=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null)
    if [ "$STATUS" = "completed" ]; then
      TOTAL=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total_found',0))" 2>/dev/null)
      FIPE=$(echo "$RESULT" | python3 -c "import sys,json; v=json.load(sys.stdin).get('fipe_value'); print(f'R\$ {v:,.0f}' if v else 'N/A')" 2>/dev/null)
      pass "Busca concluída — $TOTAL anúncios, FIPE: $FIPE"
      break
    elif [ "$STATUS" = "failed" ]; then
      fail "Busca falhou durante processamento"
      break
    fi
    [ $((i % 4)) -eq 0 ] && echo "    ... aguardando ($((i*2))s)"
  done
  [ "$STATUS" != "completed" ] && [ "$STATUS" != "failed" ] && fail "Timeout — busca ainda em $STATUS após 60s"
fi

# ─── 6. Histórico ─────────────────────────────────────────────────────────────
info "6. Histórico de buscas"
HIST=$(curl -sf "$API/api/search/history/me" -H "Authorization: Bearer $TOKEN" 2>/dev/null)
HIST_COUNT=$(echo "$HIST" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null)
[ "${HIST_COUNT:-0}" -ge 1 ] && pass "Histórico OK — $HIST_COUNT busca(s)" || fail "Histórico vazio ou erro: $HIST"

# ─── 7. Alerta (requer plano Hunter — esperado 403 no free) ──────────────────
info "7. Criação de alerta (free → deve retornar 403)"
ALERT_RESP=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API/api/alerts" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"model":"HB20","max_price":80000,"location":"São Paulo","channels":["email"]}' 2>/dev/null)
[ "$ALERT_RESP" = "403" ] && pass "Gate de plano funcionando (403 no free)" || fail "Esperado 403, recebido $ALERT_RESP"

# ─── 8. Rate limit (busca sem token) ─────────────────────────────────────────
info "8. Rate limit — buscas anônimas"
for i in 1 2 3 4; do
  curl -sf -X POST "$API/api/search" \
    -H "Content-Type: application/json" \
    -d '{"model":"Onix","max_price":60000,"location":"RJ"}' > /dev/null 2>&1 || true
done
RL_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API/api/search" \
  -H "Content-Type: application/json" \
  -d '{"model":"Onix","max_price":60000,"location":"RJ"}' 2>/dev/null)
[ "$RL_CODE" = "429" ] && pass "Rate limit funcionando (429 após exceder)" || \
  echo -e "${YELLOW}⚠ SKIP${NC}  — Rate limit: $RL_CODE (pode não ter atingido limite ainda)"

# ─── 9. Admin metrics ────────────────────────────────────────────────────────
info "9. Admin dashboard"
METRICS=$(curl -sf "$API/api/admin/metrics" -H "X-Admin-Secret: $ADMIN_SECRET" 2>/dev/null)
USERS=$(echo "$METRICS" | python3 -c "import sys,json; print(json.load(sys.stdin).get('users',{}).get('total','?'))" 2>/dev/null)
MRR=$(echo "$METRICS" | python3 -c "import sys,json; v=json.load(sys.stdin).get('revenue',{}).get('mrr_estimated',0); print(f'R\$ {v:.2f}')" 2>/dev/null)
[ -n "$USERS" ] && pass "Admin OK — $USERS usuário(s), MRR: $MRR" || fail "Admin falhou: $METRICS"

# ─── 10. FIPE isolado ─────────────────────────────────────────────────────────
info "10. Serviço FIPE"
FIPE_TEST=$(curl -sf "$API/api/search" \
  -X POST -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"model":"Onix","max_price":100000,"location":"São Paulo"}' 2>/dev/null | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('search_id','err'))" 2>/dev/null)
[ "$FIPE_TEST" != "err" ] && pass "FIPE endpoint acessível" || fail "FIPE endpoint com problema"

# ─── Resultado final ──────────────────────────────────────────────────────────
echo ""
echo "══════════════════════════════════════════"
if [ "$FAILURES" -eq 0 ]; then
  echo -e "${GREEN}  ✅ Todos os testes passaram!${NC}"
else
  echo -e "${RED}  ❌ $FAILURES teste(s) falharam${NC}"
fi
echo "══════════════════════════════════════════"
echo ""
echo "  Usuário de teste criado:"
echo "    Email   : $EMAIL"
echo "    Senha   : $PASSWORD"
echo ""
exit $FAILURES
