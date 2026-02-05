<p align="center">
  <img src="https://odinenx.vercel.app/logo.webp" alt="ODINENX" width="200"/>
</p>

<h1 align="center">ODINENX v2.0</h1>

<p align="center">
  <strong>🎯 Plataforma Inteligente de Análises Esportivas</strong>
</p>

<p align="center">
  <a href="https://odinenx.vercel.app">
    <img src="https://img.shields.io/badge/🌐_Demo-Live-00d26a?style=for-the-badge" alt="Demo"/>
  </a>
  <img src="https://img.shields.io/badge/Vue.js-3.x-4FC08D?style=for-the-badge&logo=vue.js&logoColor=white" alt="Vue 3"/>
  <img src="https://img.shields.io/badge/Supabase-Backend-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white" alt="Supabase"/>
  <img src="https://img.shields.io/badge/Vercel-Deploy-000000?style=for-the-badge&logo=vercel&logoColor=white" alt="Vercel"/>
</p>

---

## 🚀 Sobre o Projeto

**ODINENX** é uma plataforma completa para análises esportivas, integrando módulos de apostas, trading e fantasy game (Cartola FC). Com dados em tempo real e inteligência artificial, oferece insights precisos para tomada de decisão.

---

## ✨ Funcionalidades

### 🎰 Módulo BET
- Comparador de odds em tempo real
- Análise de value bets
- Histórico de apostas
- Alertas personalizados

### 📈 Módulo TRADE
- Análise de mercados financeiros
- Indicadores técnicos
- Paper trading (simulação)
- Sinais automatizados

### ⚽ Módulo Cartola FC
- Escalação automática inteligente
- **Reserva de Luxo** - Melhor substituto potencial
- Otimização de orçamento
- Análise de pontuação média

### 🔴 Jogos Ao Vivo
- Transmissão em tempo real
- 7 ligas monitoradas (Brasileirão, Premier League, La Liga, Serie A, Bundesliga, Ligue 1, Champions League)
- Dados via Football-Data.org API

---

## 🛠️ Tecnologias

| Frontend | Backend | APIs |
|----------|---------|------|
| Vue.js 3 | Supabase | Football-Data.org |
| Vue Router | PostgreSQL | Cartola FC API |
| Composition API | Edge Functions | Stripe |
| CSS3 | RLS Policies | - |

---

## 📦 Instalação

```bash
# Clone o repositório
git clone https://github.com/KevymLuccas/odinenx.git

# Entre na pasta
cd odinenx

# Instale as dependências
npm install

# Configure as variáveis de ambiente
cp .env.example .env.local

# Rode o servidor de desenvolvimento
npm run dev
```

---

## 🔐 Variáveis de Ambiente

```env
VITE_SUPABASE_URL=sua_url_supabase
VITE_SUPABASE_ANON_KEY=sua_chave_anonima
VITE_STRIPE_PUBLIC_KEY=sua_chave_stripe
VITE_FOOTBALL_API_KEY=sua_chave_football_data
```

---

## 📁 Estrutura do Projeto

```
📂 ODINENX/
├── 📂 api/              # Serverless functions (Vercel)
├── 📂 public/           # Assets estáticos
├── 📂 src/
│   ├── 📂 components/   # Componentes Vue
│   ├── 📂 lib/          # Bibliotecas (Supabase, Stripe)
│   ├── 📂 router/       # Configuração de rotas
│   └── 📂 views/        # Páginas da aplicação
│       └── 📂 modules/  # Módulos BET, TRADE, Cartola
├── 📂 supabase/
│   ├── 📂 functions/    # Edge Functions
│   └── 📂 migrations/   # Migrações SQL
└── 📄 vercel.json       # Configuração Vercel
```

---

## 🚀 Deploy

O projeto está configurado para deploy automático na **Vercel**:

```bash
# Deploy manual
vercel --prod
```

---

## 📊 Planos

| Recurso | Free | Basic | Pro | Elite |
|---------|------|-------|-----|-------|
| **Preço** | R$ 0 | R$ 19,90 | R$ 49,90 | R$ 99,90 |
| Análises/dia | 3 | ∞ | ∞ | ∞ |
| Histórico | 7 dias | 30 dias | 90 dias | ∞ |
| Salas Privadas | ❌ | 1 | 5 | ∞ |
| Módulo TRADE | ❌ | ❌ | ✅ | ✅ |
| Cartola FC | ❌ | ❌ | ✅ | ✅ |
| Alertas | ❌ | ❌ | ✅ | ✅ |
| Badge | - | 🥉 | ⭐ | 👑 |
| Suporte | - | Email | Prioritário | VIP 24/7 |

---

## 👨‍💻 Autor

Desenvolvido por **Kevym Luccas**

---

<p align="center">
  <sub>⚡ Powered by ODINENX v2.0</sub>
</p>

