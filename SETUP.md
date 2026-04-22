# Busca Carros — Deploy & Setup

## Deploy em produção (3 passos)

### Pré-requisitos
- Conta no [Render](https://render.com) (backend + banco + Redis)
- Conta no [Vercel](https://vercel.com) (frontend)
- Repositório no GitHub com o código deste projeto

---

### Passo 1 — Backend no Render

1. Acesse https://dashboard.render.com → **New → Blueprint**
2. Conecte seu repositório GitHub
3. O Render detecta o `render.yaml` automaticamente e cria:
   - Web service `buscacarros-api`
   - Worker `buscacarros-worker` (Celery)
   - Worker `buscacarros-beat` (scheduler)
   - PostgreSQL `buscacarros-db`
   - Redis `buscacarros-redis`
4. Configure as variáveis marcadas como `sync: false` no dashboard:

| Variável | Onde obter |
|---|---|
| `ANTHROPIC_API_KEY` | https://console.anthropic.com |
| `STRIPE_SECRET_KEY` | https://dashboard.stripe.com/apikeys |
| `STRIPE_WEBHOOK_SECRET` | https://dashboard.stripe.com/webhooks |
| `STRIPE_PRICE_HUNTER` | ID do produto no Stripe |
| `STRIPE_PRICE_HUNTER_PRO` | ID do produto no Stripe |
| `STRIPE_PRICE_DEALER` | ID do produto no Stripe |
| `RESEND_API_KEY` | https://resend.com |
| `TELEGRAM_BOT_TOKEN` | @BotFather no Telegram |
| `APP_URL` | URL do frontend Vercel (passo 2) |

5. URL do backend: `https://buscacarros-api.onrender.com`

---

### Passo 2 — Frontend no Vercel

```bash
cd frontend
npm install -g vercel
vercel login
vercel --prod
# Quando perguntar, configure:
#   Build Command: npm run build
#   Output: dist
#   Framework: Vite
```

Após o deploy, adicione a env var no Vercel:
```bash
vercel env add VITE_API_URL production
# Cole: https://buscacarros-api.onrender.com

vercel --prod  # re-deploy com a var
```

---

### Passo 3 — Stripe Webhook

No dashboard Stripe → Webhooks → Add endpoint:
```
URL: https://buscacarros-api.onrender.com/api/subscriptions/webhook
Eventos: checkout.session.completed, customer.subscription.updated,
         customer.subscription.deleted, invoice.payment_failed
```

Copie o `Webhook Signing Secret` e adicione como `STRIPE_WEBHOOK_SECRET` no Render.

---

## Deploy automatizado (script)

```bash
bash deploy.sh
```
O script instala Vercel CLI, faz build, deploy e configura a env var automaticamente.
Render ainda requer acesso manual ao dashboard (sem CLI open-source gratuito).

---

## Teste de integração

Após o deploy, valide o fluxo completo:

```bash
bash test-integration.sh https://buscacarros-api.onrender.com SEU_ADMIN_SECRET
```

O script testa:
1. Health check da API
2. Cadastro de usuário
3. Login
4. Busca de veículo
5. Polling de resultados
6. Histórico
7. Gate de plano (alerta requer Hunter)
8. Rate limit (free = 3/dia)
9. Admin dashboard

---

## Desenvolvimento local

```bash
# Opção 1 — Docker (recomendado)
cp backend/.env.example backend/.env
# Edite .env com ANTHROPIC_API_KEY
docker-compose up --build

# Opção 2 — Manual
# Terminal 1 (backend)
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload

# Terminal 2 (worker)
cd backend && celery -A app.workers.celery_app worker --loglevel=info

# Terminal 3 (frontend)
cd frontend && npm install && npm run dev
```

Acesse: http://localhost:5173 | API Docs: http://localhost:8000/docs

---

## URLs de produção

| Serviço | URL |
|---|---|
| Frontend | `https://busca-carros.vercel.app` |
| Backend API | `https://buscacarros-api.onrender.com` |
| API Docs | `https://buscacarros-api.onrender.com/docs` |
| Admin | `https://busca-carros.vercel.app/admin` |
| Health | `https://buscacarros-api.onrender.com/health` |

---

## Credenciais admin

O painel admin em `/admin` usa o header `X-Admin-Secret`.
Valor definido pela variável `ADMIN_SECRET` no Render (gerado automaticamente).

Para consultar:
```bash
render env get ADMIN_SECRET --service buscacarros-api
```

Ou diretamente no Render Dashboard → Environment.
