# Roadmap Mobile — Busca Carros

## Estratégia: API-first já implementada

A API FastAPI atual já está pronta para suportar mobile sem alterações.
O app mobile consumirá os mesmos endpoints REST do web.

---

## Stack recomendada: React Native + Expo

```
mobile/
├── app/                    ← Expo Router (file-based routing)
│   ├── (tabs)/
│   │   ├── index.tsx       ← Busca (SearchForm nativo)
│   │   ├── results.tsx     ← Ranking com FlatList
│   │   ├── alerts.tsx      ← Alertas (mesma lógica)
│   │   └── profile.tsx     ← Conta e assinatura
│   ├── dealer/             ← Portal lojista mobile
│   └── _layout.tsx
├── components/             ← CarCard nativo, ResaleCard nativo
├── services/
│   └── api.ts              ← Reaproveitado do web (mesmas chamadas)
└── app.json
```

### Justificativa React Native + Expo
- **Reaproveitamento de 70% do código**: lógica de negócio, tipos TypeScript e chamadas API são idênticos
- **Expo EAS Build**: CI/CD gratuito para iOS e Android
- **Push Notifications nativas**: integrar com Expo Notifications para substituir/complementar WhatsApp/Telegram
- **OTA Updates**: deploy de atualizações sem publicar nova versão na loja

---

## Funcionalidades exclusivas mobile

| Feature | Implementação |
|---|---|
| Push Notifications | Expo Push Notifications + tabela `push_tokens` no backend |
| Busca por voz | Expo Speech → preenche o formulário |
| Câmera para placa | expo-camera + OCR → busca automática pelo modelo |
| Localização automática | expo-location → preenche cidade/estado |
| Compartilhar anúncio | Expo Sharing → gera card social do veículo |
| Widget iOS/Android | expo-widgets → alerta de preço na tela inicial |
| Modo offline | AsyncStorage → salva última busca |

---

## Backend: adições necessárias para mobile

### 1. Push token endpoint (já pronto para adicionar)
```python
# app/routers/mobile.py
@router.post("/push-token")
async def register_push_token(token: str, platform: str, ...):
    # salva em tabela push_tokens
```

### 2. Envio de push no alert_service.py
```python
# Adicionar ao alert_service.py após os canais existentes:
if "push" in channels:
    await send_expo_push(user.push_token, message)
```

### 3. Endpoint de autenticação com Google/Apple (OAuth)
```python
# Usuário mobile raramente usa e-mail/senha
# Adicionar: POST /api/auth/google, POST /api/auth/apple
```

---

## Monetização mobile

- **IAP (In-App Purchase)** via RevenueCat SDK
  - RevenueCat sincroniza automaticamente com Stripe (web) e Google Play / App Store (mobile)
  - Usuário assina em qualquer plataforma e acessa em todas
- Regra: se já tem assinatura Stripe ativa, ignorar IAP — mostrar badge "Assinante Web"

---

## Cronograma sugerido

| Fase | Entregável | Estimativa |
|---|---|---|
| MVP Mobile | Busca + Resultados + Auth | 3 semanas |
| Push Notifications | Alertas via push | 1 semana |
| Dealer mobile | Portal lojista | 2 semanas |
| Câmera OCR | Busca por placa | 2 semanas |
| Lançamento lojas | iOS App Store + Google Play | 1 semana |

**Total estimado até lançamento:** ~2 meses após início do desenvolvimento mobile.

---

## Checklist antes de iniciar mobile

- [ ] Backend rodando em produção (Railway / Render / AWS)
- [ ] Domínio configurado com HTTPS
- [ ] Auth funcionando (JWT)
- [ ] Stripe em produção (não test mode)
- [ ] Variáveis de ambiente de produção configuradas
- [ ] Criar conta Apple Developer ($99/ano) e Google Play Console ($25 único)
