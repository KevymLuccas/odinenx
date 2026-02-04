<script setup>
/**
 * 💰 Pricing.vue - Nova Precificação v2.0
 * ODINENX - Planos com recursos sociais
 */

import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../lib/supabase'
import { plans, redirectToCheckout, getSubscriptionStatus, getPlanBadge } from '../lib/stripe'

const router = useRouter()
const user = ref(null)
const currentPlan = ref('free')
const loading = ref(false)
const loadingPlan = ref(null)
const error = ref('')
const billingCycle = ref('monthly')

onMounted(async () => {
  const { data: { session } } = await supabase.auth.getSession()
  user.value = session?.user ?? null
  
  if (user.value) {
    const subscription = await getSubscriptionStatus(user.value.id)
    currentPlan.value = subscription.plan || 'free'
  }
})

const handleSubscribe = async (planId) => {
  try {
    if (!user.value) {
      router.push('/register')
      return
    }
    
    if (planId === 'free') return
    if (planId === currentPlan.value) return
    
    loadingPlan.value = planId
    error.value = ''
    
    await redirectToCheckout(planId)
  } catch (err) {
    error.value = err.message
  } finally {
    loadingPlan.value = null
  }
}

// Planos para exibição
const plansList = computed(() => Object.values(plans))

// Preço com desconto anual
const getPrice = (plan) => {
  if (billingCycle.value === 'annual') {
    return Math.round(plan.price * 0.8 * 100) / 100
  }
  return plan.price
}

// Recursos v2.0 para comparativo
const v2Features = [
  { name: 'Salas ao Vivo', free: '✓', basic: '✓', pro: '✓', elite: '✓' },
  { name: 'Chat em tempo real', free: 'Texto', basic: 'Texto + Emoji', pro: '+ GIFs', elite: '+ Stickers' },
  { name: 'Badge exclusivo', free: '—', basic: '🥉 Bronze', pro: '⭐ Ouro', elite: '👑 Coroa' },
  { name: 'Posição na lista', free: 'Última', basic: '3ª posição', pro: '2ª posição', elite: '1ª posição' },
  { name: 'Salas privadas', free: '—', basic: '1 sala', pro: '5 salas', elite: 'Ilimitado' },
  { name: 'Celebração de gols', free: 'Básica', basic: 'Confetes', pro: '+ Estrelas', elite: '+ Efeitos VIP' },
  { name: 'Loja de customização', free: '—', basic: '—', pro: '—', elite: '✓' },
  { name: 'Análises por dia', free: '3', basic: 'Ilimitado', pro: 'Ilimitado', elite: 'Ilimitado' },
  { name: 'Histórico', free: '7 dias', basic: '30 dias', pro: '90 dias', elite: 'Ilimitado' },
  { name: 'IA Avançada', free: '—', basic: '—', pro: '✓', elite: '✓' },
  { name: 'Alertas tempo real', free: '—', basic: '—', pro: '✓', elite: '✓' },
  { name: 'Paper Trading', free: '—', basic: '—', pro: '✓', elite: '✓' },
  { name: 'Suporte prioritário', free: '—', basic: '—', pro: '—', elite: '✓' }
]
</script>

<template>
  <div class="pricing-page">
    <!-- Header -->
    <header class="pricing-header">
      <router-link to="/" class="back-link">
        <img src="/logo.webp" alt="ODINENX" class="header-logo" />
      </router-link>
    </header>

    <main class="pricing-main">
      <!-- Hero -->
      <div class="pricing-hero">
        <div class="version-badge">v2.0</div>
        <h1>Escolha seu <span class="gradient-text">plano</span></h1>
        <p>Experiência social de apostas com chat ao vivo</p>
        
        <!-- Toggle Mensal/Anual -->
        <div class="billing-toggle">
          <span :class="{ active: billingCycle === 'monthly' }">Mensal</span>
          <button 
            class="toggle-btn" 
            :class="{ annual: billingCycle === 'annual' }"
            @click="billingCycle = billingCycle === 'monthly' ? 'annual' : 'monthly'"
          >
            <span class="toggle-indicator"></span>
          </button>
          <span :class="{ active: billingCycle === 'annual' }">
            Anual
            <span class="discount-badge">-20%</span>
          </span>
        </div>
      </div>

      <!-- Error -->
      <div v-if="error" class="error-banner">
        {{ error }}
      </div>

      <!-- Plans Grid -->
      <div class="plans-grid">
        <div 
          v-for="plan in plansList" 
          :key="plan.id"
          class="plan-card"
          :class="{ 
            popular: plan.popular, 
            current: currentPlan === plan.id,
            elite: plan.id === 'elite'
          }"
        >
          <!-- Badges -->
          <div v-if="plan.popular" class="popular-badge">🔥 MAIS POPULAR</div>
          <div v-if="currentPlan === plan.id" class="current-badge">SEU PLANO</div>
          
          <!-- Plan Header -->
          <div class="plan-header">
            <div class="plan-badge" v-if="plan.badgeEmoji">
              {{ plan.badgeEmoji }}
            </div>
            <h3>{{ plan.name }}</h3>
            <div class="plan-price">
              <span class="currency">R$</span>
              <span class="amount">{{ getPrice(plan).toFixed(2).replace('.', ',') }}</span>
              <span class="period" v-if="plan.price > 0">/mês</span>
            </div>
            <p class="plan-billing" v-if="plan.price > 0 && billingCycle === 'annual'">
              Cobrado R$ {{ (getPrice(plan) * 12).toFixed(2).replace('.', ',') }}/ano
            </p>
          </div>

          <!-- Features -->
          <ul class="plan-features">
            <li v-for="feature in plan.features" :key="feature">
              <span class="check">✓</span>
              {{ feature }}
            </li>
          </ul>

          <!-- v2.0 Highlights -->
          <div class="v2-highlights" v-if="plan.id !== 'free'">
            <div class="v2-tag">Novo v2.0</div>
            <div class="highlights-list">
              <span v-if="plan.limits?.gifs">📱 GIFs no chat</span>
              <span v-if="plan.limits?.stickers">🎨 Stickers exclusivos</span>
              <span v-if="plan.limits?.salasPrivadas > 0">🔒 Salas privadas</span>
              <span v-if="plan.limits?.celebracao !== 'basic'">🎉 Celebrações VIP</span>
            </div>
          </div>

          <!-- CTA Button -->
          <button 
            class="plan-btn"
            :class="{ 
              primary: plan.popular,
              elite: plan.id === 'elite',
              disabled: currentPlan === plan.id 
            }"
            :disabled="loadingPlan === plan.id || currentPlan === plan.id"
            @click="handleSubscribe(plan.id)"
          >
            <span v-if="loadingPlan === plan.id" class="spinner"></span>
            <span v-else-if="currentPlan === plan.id">Plano Atual</span>
            <span v-else-if="plan.price === 0">Começar Grátis</span>
            <span v-else>
              Assinar {{ plan.name }}
              <span class="btn-badge" v-if="plan.badgeEmoji">{{ plan.badgeEmoji }}</span>
            </span>
          </button>
        </div>
      </div>

      <!-- Features Comparison -->
      <section class="features-section">
        <h2>🆚 Comparativo completo</h2>
        
        <div class="features-table">
          <div class="table-header">
            <div class="feature-name">Recursos</div>
            <div class="plan-col">Free</div>
            <div class="plan-col">Basic 🥉</div>
            <div class="plan-col highlight">Pro ⭐</div>
            <div class="plan-col elite">Elite 👑</div>
          </div>
          
          <div 
            v-for="feature in v2Features" 
            :key="feature.name"
            class="table-row"
          >
            <div class="feature-name">{{ feature.name }}</div>
            <div class="plan-col">{{ feature.free }}</div>
            <div class="plan-col">{{ feature.basic }}</div>
            <div class="plan-col highlight">{{ feature.pro }}</div>
            <div class="plan-col elite">{{ feature.elite }}</div>
          </div>
        </div>
      </section>

      <!-- FAQ -->
      <section class="faq-section">
        <h2>❓ Perguntas Frequentes</h2>
        
        <div class="faq-grid">
          <div class="faq-item">
            <h4>O que são as salas ao vivo?</h4>
            <p>São espaços onde você assiste jogos junto com outros apostadores, compartilhando suas odds e comemorando gols em tempo real.</p>
          </div>
          
          <div class="faq-item">
            <h4>Como funcionam os badges?</h4>
            <p>Cada plano tem um badge exclusivo que aparece ao lado do seu nome no chat. Quanto maior o plano, mais destaque você terá!</p>
          </div>
          
          <div class="faq-item">
            <h4>O que são salas privadas?</h4>
            <p>Você pode criar salas exclusivas e convidar amigos usando um código. Perfeito para assistir jogos com seu grupo!</p>
          </div>
          
          <div class="faq-item">
            <h4>Como funciona a loja de customização?</h4>
            <p>Usuários Elite podem comprar efeitos especiais, cores personalizadas e muito mais para se destacar nas salas.</p>
          </div>
          
          <div class="faq-item">
            <h4>Posso trocar de plano?</h4>
            <p>Sim! Você pode fazer upgrade ou downgrade a qualquer momento. O valor será ajustado proporcionalmente.</p>
          </div>
          
          <div class="faq-item">
            <h4>Como cancelo minha assinatura?</h4>
            <p>Basta acessar Configurações {'>'} Assinatura e clicar em "Cancelar". Você mantém acesso até o fim do período pago.</p>
          </div>
        </div>
      </section>

      <!-- CTA Final -->
      <section class="final-cta">
        <h2>🚀 Pronto para começar?</h2>
        <p>Junte-se a milhares de apostadores na experiência social definitiva</p>
        <div class="cta-buttons">
          <button class="btn-primary" @click="handleSubscribe('pro')">
            Assinar Pro ⭐
          </button>
          <router-link to="/live" class="btn-secondary">
            Experimentar Grátis
          </router-link>
        </div>
      </section>
    </main>

    <!-- Footer -->
    <footer class="pricing-footer">
      <p>© 2025 ODINENX. Todos os direitos reservados.</p>
      <div class="footer-links">
        <a href="#">Termos de Uso</a>
        <a href="#">Política de Privacidade</a>
        <a href="#">Contato</a>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.pricing-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%);
  color: white;
}

/* Header */
.pricing-header {
  padding: 1.5rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-logo {
  height: 40px;
}

/* Main */
.pricing-main {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}

/* Hero */
.pricing-hero {
  text-align: center;
  margin-bottom: 4rem;
}

.version-badge {
  display: inline-block;
  background: linear-gradient(135deg, #ffd700 0%, #ff8c00 100%);
  color: #000;
  padding: 0.25rem 1rem;
  border-radius: 20px;
  font-weight: 700;
  font-size: 0.9rem;
  margin-bottom: 1rem;
}

.pricing-hero h1 {
  font-size: 3rem;
  margin: 0 0 1rem 0;
}

.gradient-text {
  background: linear-gradient(135deg, #ffd700 0%, #ff8c00 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.pricing-hero > p {
  color: #888;
  font-size: 1.2rem;
}

/* Billing Toggle */
.billing-toggle {
  display: inline-flex;
  align-items: center;
  gap: 1rem;
  margin-top: 2rem;
  padding: 0.5rem 1.5rem;
  background: rgba(255,255,255,0.05);
  border-radius: 50px;
}

.billing-toggle span {
  color: #666;
  transition: color 0.3s;
}

.billing-toggle span.active {
  color: white;
}

.toggle-btn {
  width: 50px;
  height: 26px;
  background: rgba(255,255,255,0.1);
  border: none;
  border-radius: 13px;
  position: relative;
  cursor: pointer;
  transition: background 0.3s;
}

.toggle-btn.annual {
  background: linear-gradient(135deg, #ffd700 0%, #ff8c00 100%);
}

.toggle-indicator {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 20px;
  height: 20px;
  background: white;
  border-radius: 50%;
  transition: transform 0.3s;
}

.toggle-btn.annual .toggle-indicator {
  transform: translateX(24px);
}

.discount-badge {
  background: #00c853;
  color: white;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  margin-left: 0.5rem;
}

/* Error Banner */
.error-banner {
  background: rgba(255,68,68,0.1);
  border: 1px solid rgba(255,68,68,0.3);
  color: #ff4444;
  padding: 1rem;
  border-radius: 10px;
  text-align: center;
  margin-bottom: 2rem;
}

/* Plans Grid */
.plans-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.5rem;
  margin-bottom: 4rem;
}

/* Plan Card */
.plan-card {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 20px;
  padding: 2rem;
  position: relative;
  transition: all 0.3s;
}

.plan-card:hover {
  transform: translateY(-5px);
  border-color: rgba(255,215,0,0.3);
}

.plan-card.popular {
  border-color: #ffd700;
  box-shadow: 0 0 30px rgba(255,215,0,0.2);
}

.plan-card.elite {
  background: linear-gradient(135deg, rgba(138,43,226,0.1) 0%, rgba(255,215,0,0.1) 100%);
  border-color: rgba(138,43,226,0.5);
}

.plan-card.current {
  border-color: #00c853;
}

/* Badges */
.popular-badge {
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  background: linear-gradient(135deg, #ffd700 0%, #ff8c00 100%);
  color: #000;
  padding: 0.25rem 1rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 700;
}

.current-badge {
  position: absolute;
  top: -12px;
  right: 1rem;
  background: #00c853;
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.7rem;
  font-weight: 600;
}

/* Plan Header */
.plan-header {
  text-align: center;
  margin-bottom: 1.5rem;
}

.plan-badge {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.plan-header h3 {
  font-size: 1.5rem;
  margin: 0 0 1rem 0;
}

.plan-price {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 0.25rem;
}

.currency {
  font-size: 1.2rem;
  color: #888;
}

.amount {
  font-size: 2.5rem;
  font-weight: 700;
}

.period {
  color: #888;
  font-size: 0.9rem;
}

.plan-billing {
  color: #666;
  font-size: 0.8rem;
  margin-top: 0.5rem;
}

/* Features */
.plan-features {
  list-style: none;
  padding: 0;
  margin: 0 0 1.5rem 0;
}

.plan-features li {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0;
  font-size: 0.9rem;
  color: #ccc;
}

.check {
  color: #00c853;
  font-weight: 600;
}

/* v2.0 Highlights */
.v2-highlights {
  background: rgba(255,215,0,0.05);
  border-radius: 10px;
  padding: 1rem;
  margin-bottom: 1.5rem;
}

.v2-tag {
  font-size: 0.7rem;
  color: #ffd700;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.highlights-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.highlights-list span {
  font-size: 0.8rem;
  color: #aaa;
}

/* CTA Button */
.plan-btn {
  width: 100%;
  padding: 1rem;
  border: none;
  border-radius: 10px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  background: rgba(255,255,255,0.1);
  color: white;
}

.plan-btn:hover:not(.disabled) {
  background: rgba(255,255,255,0.2);
}

.plan-btn.primary {
  background: linear-gradient(135deg, #ffd700 0%, #ff8c00 100%);
  color: #000;
}

.plan-btn.primary:hover:not(.disabled) {
  transform: scale(1.02);
  box-shadow: 0 5px 20px rgba(255,215,0,0.3);
}

.plan-btn.elite {
  background: linear-gradient(135deg, #8a2be2 0%, #ffd700 100%);
  color: white;
}

.plan-btn.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-badge {
  font-size: 1rem;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Features Section */
.features-section {
  margin-bottom: 4rem;
}

.features-section h2 {
  text-align: center;
  font-size: 2rem;
  margin-bottom: 2rem;
}

.features-table {
  background: rgba(255,255,255,0.03);
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.1);
}

.table-header {
  display: grid;
  grid-template-columns: 2fr repeat(4, 1fr);
  background: rgba(255,255,255,0.05);
  font-weight: 600;
}

.table-row {
  display: grid;
  grid-template-columns: 2fr repeat(4, 1fr);
  border-top: 1px solid rgba(255,255,255,0.05);
}

.feature-name {
  padding: 1rem 1.5rem;
  text-align: left;
}

.plan-col {
  padding: 1rem;
  text-align: center;
  color: #aaa;
}

.plan-col.highlight {
  background: rgba(255,215,0,0.05);
  color: #ffd700;
}

.plan-col.elite {
  background: rgba(138,43,226,0.05);
  color: #da70d6;
}

/* FAQ Section */
.faq-section {
  margin-bottom: 4rem;
}

.faq-section h2 {
  text-align: center;
  font-size: 2rem;
  margin-bottom: 2rem;
}

.faq-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
}

.faq-item {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 16px;
  padding: 1.5rem;
}

.faq-item h4 {
  margin: 0 0 0.75rem 0;
  font-size: 1rem;
}

.faq-item p {
  margin: 0;
  color: #888;
  font-size: 0.9rem;
  line-height: 1.6;
}

/* Final CTA */
.final-cta {
  text-align: center;
  padding: 4rem 2rem;
  background: linear-gradient(135deg, rgba(255,215,0,0.05) 0%, rgba(255,140,0,0.05) 100%);
  border-radius: 24px;
  margin-bottom: 4rem;
}

.final-cta h2 {
  font-size: 2rem;
  margin: 0 0 0.5rem 0;
}

.final-cta p {
  color: #888;
  margin: 0 0 2rem 0;
}

.cta-buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.btn-primary {
  background: linear-gradient(135deg, #ffd700 0%, #ff8c00 100%);
  color: #000;
  font-weight: 600;
  padding: 1rem 2rem;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.3s;
}

.btn-primary:hover {
  transform: scale(1.05);
}

.btn-secondary {
  background: transparent;
  color: white;
  font-weight: 600;
  padding: 1rem 2rem;
  border: 1px solid rgba(255,255,255,0.3);
  border-radius: 10px;
  text-decoration: none;
  transition: all 0.3s;
}

.btn-secondary:hover {
  background: rgba(255,255,255,0.1);
}

/* Footer */
.pricing-footer {
  text-align: center;
  padding: 2rem;
  border-top: 1px solid rgba(255,255,255,0.05);
}

.pricing-footer p {
  color: #666;
  margin: 0 0 1rem 0;
}

.footer-links {
  display: flex;
  gap: 2rem;
  justify-content: center;
}

.footer-links a {
  color: #888;
  text-decoration: none;
  font-size: 0.9rem;
}

.footer-links a:hover {
  color: white;
}

/* Responsive */
@media (max-width: 1200px) {
  .plans-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .pricing-main {
    padding: 1rem;
  }
  
  .pricing-hero h1 {
    font-size: 2rem;
  }
  
  .plans-grid {
    grid-template-columns: 1fr;
  }
  
  .faq-grid {
    grid-template-columns: 1fr;
  }
  
  .table-header,
  .table-row {
    grid-template-columns: 1.5fr repeat(4, 1fr);
    font-size: 0.75rem;
  }
  
  .feature-name {
    padding: 0.75rem;
  }
  
  .plan-col {
    padding: 0.75rem 0.25rem;
  }
  
  .cta-buttons {
    flex-direction: column;
  }
}
</style>
