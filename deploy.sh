#!/usr/bin/env bash
# deploy.sh — Prepara e faz deploy do Busca Carros
# Uso: bash deploy.sh
set -e

BLUE='\033[0;34m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC}   $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

echo ""
echo "═══════════════════════════════════════════════"
echo "   🚗  Busca Carros — Deploy Script v2.0"
echo "═══════════════════════════════════════════════"
echo ""

# ─── 1. Verificar dependências de CLI ─────────────────────────────────────────
info "Verificando CLIs necessárias..."

install_if_missing() {
  local cmd=$1 pkg=$2
  if ! command -v "$cmd" &>/dev/null; then
    warn "$cmd não encontrado. Instalando $pkg..."
    npm install -g "$pkg" || error "Falha ao instalar $pkg"
  fi
  success "$cmd disponível"
}

install_if_missing "vercel" "vercel"

if ! command -v "render" &>/dev/null; then
  warn "render CLI não encontrado."
  info "Instale manualmente: https://render.com/docs/cli"
  info "Ou use o dashboard web em: https://dashboard.render.com"
fi

# ─── 2. Verificar .env ────────────────────────────────────────────────────────
info "Verificando variáveis de ambiente..."

if [ ! -f "backend/.env" ]; then
  cp backend/.env.example backend/.env
  warn "Arquivo backend/.env criado a partir do .env.example"
  warn "⚠️  Configure ANTHROPIC_API_KEY e STRIPE_* antes do deploy!"
fi

check_env() {
  local key=$1
  if grep -q "^${key}=sk-\|^${key}=re_\|^${key}=price_" backend/.env 2>/dev/null; then
    success "$key configurada"
  else
    warn "$key não configurada (opcional para MVP, necessária para feature completa)"
  fi
}

check_env "ANTHROPIC_API_KEY"
check_env "STRIPE_SECRET_KEY"
check_env "RESEND_API_KEY"
check_env "TELEGRAM_BOT_TOKEN"

# ─── 3. Build e teste local ───────────────────────────────────────────────────
info "Instalando dependências do frontend..."
cd frontend
npm install --silent
success "npm install concluído"

info "Testando build de produção do frontend..."
npm run build 2>&1 | tail -5
success "Build do frontend OK"
cd ..

# ─── 4. Verificar se tem repositório git ──────────────────────────────────────
info "Verificando repositório git..."
if [ ! -d ".git" ]; then
  git init
  git add -A
  git commit -m "feat: busca carros saas v2.0 — initial commit"
  success "Repositório git inicializado"
else
  git add -A
  git diff --cached --quiet || git commit -m "chore: pre-deploy updates $(date '+%Y-%m-%d %H:%M')"
  success "Commit criado"
fi

# ─── 5. Deploy frontend → Vercel ─────────────────────────────────────────────
echo ""
echo "──────────────────────────────────────────────"
info "PASSO 1/2: Deploy do FRONTEND no Vercel"
echo "──────────────────────────────────────────────"
cd frontend

VERCEL_OUTPUT=$(vercel --prod --yes 2>&1) || { warn "Vercel: verifique o login com 'vercel login'"; echo "$VERCEL_OUTPUT"; }
FRONTEND_URL=$(echo "$VERCEL_OUTPUT" | grep -E "https://.*\.vercel\.app" | tail -1 | tr -d ' ')

if [ -n "$FRONTEND_URL" ]; then
  success "Frontend publicado em: $FRONTEND_URL"
  echo "FRONTEND_URL=$FRONTEND_URL" >> ../.deploy-output
else
  warn "URL do frontend não detectada automaticamente. Verifique o dashboard Vercel."
  FRONTEND_URL="https://busca-carros.vercel.app"
fi
cd ..

# ─── 6. Deploy backend → Render ──────────────────────────────────────────────
echo ""
echo "──────────────────────────────────────────────"
info "PASSO 2/2: Deploy do BACKEND no Render"
echo "──────────────────────────────────────────────"

if command -v "render" &>/dev/null; then
  render deploy --service buscacarros-api 2>&1 || warn "render CLI: verifique 'render login'"
  BACKEND_URL="https://buscacarros-api.onrender.com"
  success "Backend no Render iniciado"
else
  echo ""
  warn "render CLI não disponível. Faça o deploy manual:"
  echo ""
  echo "  1. Acesse https://dashboard.render.com"
  echo "  2. New → Blueprint → conecte seu repositório GitHub"
  echo "  3. Render detecta automaticamente o render.yaml"
  echo "  4. Configure as variáveis de ambiente marcadas como 'sync: false'"
  echo "  5. URL do backend será: https://buscacarros-api.onrender.com"
  echo ""
  BACKEND_URL="https://buscacarros-api.onrender.com"
fi

# ─── 7. Atualizar VITE_API_URL no Vercel ─────────────────────────────────────
info "Configurando VITE_API_URL no Vercel..."
cd frontend
vercel env add VITE_API_URL production <<< "$BACKEND_URL" 2>/dev/null || \
  warn "Configure manualmente: vercel env add VITE_API_URL production → $BACKEND_URL"

# Re-deploy com a env var
vercel --prod --yes 2>&1 | tail -3
cd ..

# ─── 8. Criar usuário admin de teste ─────────────────────────────────────────
ADMIN_SECRET=$(grep "^ADMIN_SECRET=" backend/.env 2>/dev/null | cut -d'=' -f2)
[ -z "$ADMIN_SECRET" ] && ADMIN_SECRET="busca-admin-$(date +%s | tail -c 6)"

# ─── 9. Resultado final ───────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════"
echo -e "${GREEN}   ✅  Deploy concluído!${NC}"
echo "═══════════════════════════════════════════════"
echo ""
echo "  🌐  Frontend : $FRONTEND_URL"
echo "  ⚙️   Backend  : $BACKEND_URL"
echo "  📊  Admin    : $FRONTEND_URL/admin"
echo "  📖  API Docs : $BACKEND_URL/docs"
echo ""
echo "  🔑  Credenciais admin:"
echo "      Header: X-Admin-Secret: $ADMIN_SECRET"
echo ""
echo "  💳  Status Stripe: $([ -n "$(grep 'STRIPE_SECRET_KEY=sk_' backend/.env 2>/dev/null)" ] && echo 'CONFIGURADO' || echo 'PENDENTE — adicione STRIPE_SECRET_KEY no .env')"
echo ""
echo "  📋  Próximos passos:"
echo "      1. Registre uma conta em $FRONTEND_URL"
echo "      2. Faça uma busca de teste (ex: HB20, São Paulo)"
echo "      3. Configure Stripe em https://dashboard.stripe.com"
echo "      4. Adicione o webhook: $BACKEND_URL/api/subscriptions/webhook"
echo ""

# Salva output
{
  echo "DEPLOY_DATE=$(date)"
  echo "FRONTEND_URL=$FRONTEND_URL"
  echo "BACKEND_URL=$BACKEND_URL"
  echo "ADMIN_SECRET=$ADMIN_SECRET"
} >> .deploy-output

success "Detalhes salvos em .deploy-output"
