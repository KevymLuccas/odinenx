# 📦 Guia de Deploy - ODINENX

## 🔧 Passo 1: Configurar Stripe Dashboard

### Criar Produtos e Preços no Stripe:

1. Acesse https://dashboard.stripe.com/products
2. Crie 3 produtos (Basic, Pro, Elite):

**Basic - R$79/mês**
- Nome: ODINENX Basic
- Preço: R$ 79,00 / mês
- Após criar, copie o `price_id` (ex: price_1ABC...)

**Pro - R$199/mês**
- Nome: ODINENX Pro
- Preço: R$ 199,00 / mês
- Copie o `price_id`

**Elite - R$399/mês**
- Nome: ODINENX Elite
- Preço: R$ 399,00 / mês
- Copie o `price_id`

3. Atualize os `stripePriceId` no arquivo `src/lib/stripe.js`:
```javascript
basic: {
  stripePriceId: 'price_SEU_ID_AQUI',
  // ...
},
pro: {
  stripePriceId: 'price_SEU_ID_AQUI',
  // ...
},
elite: {
  stripePriceId: 'price_SEU_ID_AQUI',
  // ...
}
```

---

## 🗄️ Passo 2: Configurar Supabase Database

1. Acesse seu projeto Supabase: https://app.supabase.com/project/mzamszcpbverpadjelck
2. Vá em **SQL Editor**
3. Cole e execute o conteúdo do arquivo:
   `supabase/migrations/001_initial_schema.sql`

---

## ⚡ Passo 3: Deploy das Edge Functions

### Instalar Supabase CLI (se não tiver):
```bash
npm install -g supabase
```

### Login no Supabase:
```bash
supabase login
```

### Linkar o projeto:
```bash
cd C:\Users\kevym.novais\Downloads\ODIENX
supabase link --project-ref mzamszcpbverpadjelck
```

### Definir secrets (variáveis de ambiente):
```bash
supabase secrets set STRIPE_SECRET_KEY=your_stripe_secret_key_here

supabase secrets set STRIPE_WEBHOOK_SECRET=whsec_SEU_WEBHOOK_SECRET
```

### Deploy das funções:
```bash
supabase functions deploy create-checkout
supabase functions deploy customer-portal
supabase functions deploy stripe-webhook
```

---

## 🔔 Passo 4: Configurar Webhook no Stripe

1. Acesse https://dashboard.stripe.com/webhooks
2. Clique em **+ Add endpoint**
3. URL do endpoint:
   ```
   https://mzamszcpbverpadjelck.supabase.co/functions/v1/stripe-webhook
   ```
4. Eventos para escutar:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`

5. Após criar, copie o **Signing secret** (começa com `whsec_`)
6. Atualize o secret:
   ```bash
   supabase secrets set STRIPE_WEBHOOK_SECRET=whsec_SEU_SECRET_AQUI
   ```

---

## 🌐 Passo 5: Deploy na Vercel

```bash
cd C:\Users\kevym.novais\Downloads\ODIENX
npm run build
vercel --prod
```

---

## ✅ Checklist Final

- [ ] Produtos criados no Stripe
- [ ] Price IDs atualizados no código
- [ ] Tabelas criadas no Supabase
- [ ] Edge Functions deployadas
- [ ] Webhook configurado no Stripe
- [ ] Secrets configurados (STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET)
- [ ] Site deployado na Vercel

---

## 🧪 Testar o Fluxo

1. Acesse o site
2. Crie uma conta
3. Vá em /pricing
4. Clique em um plano
5. Complete o checkout (use cartão de teste 4242 4242 4242 4242)
6. Verifique se a assinatura aparece no dashboard
