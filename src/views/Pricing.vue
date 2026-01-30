<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../lib/supabase'
import { plans, redirectToCheckout, getSubscriptionStatus } from '../lib/stripe'

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

const plansList = Object.values(plans)
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
      <div class="pricing-hero">
        <h1>Escolha seu <span class="gradient-text">plano</span></h1>
        <p>Comece grátis. Evolua quando quiser. Cancele a qualquer momento.</p>
        
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
            current: currentPlan === plan.id 
          }"
        >
          <div v-if="plan.popular" class="popular-badge">MAIS POPULAR</div>
          <div v-if="currentPlan === plan.id" class="current-badge">PLANO ATUAL</div>
          
          <div class="plan-header">
            <h3>{{ plan.name }}</h3>
            <div class="plan-price">
              <span class="currency">R$</span>
              <span class="amount">
                {{ billingCycle === 'annual' ? Math.round(plan.price * 0.8) : plan.price }}
              </span>
              <span class="period" v-if="plan.price > 0">/mês</span>
            </div>
            <p class="plan-billing" v-if="plan.price > 0 && billingCycle === 'annual'">
              Cobrado R$ {{ Math.round(plan.price * 0.8 * 12) }}/ano
            </p>
          </div>

          <ul class="plan-features">
            <li v-for="feature in plan.features" :key="feature">
              <span class="check">✓</span>
              {{ feature }}
            </li>
          </ul>

          <button 
            class="plan-btn"
            :class="{ 
              primary: plan.popular,
              disabled: currentPlan === plan.id 
            }"
            :disabled="loadingPlan === plan.id || currentPlan === plan.id"
            @click="handleSubscribe(plan.id)"
          >
            <span v-if="loadingPlan === plan.id" class="spinner"></span>
            <span v-else-if="currentPlan === plan.id">Plano Atual</span>
            <span v-else-if="plan.price === 0">Começar Grátis</span>
            <span v-else>Assinar {{ plan.name }}</span>
          </button>
        </div>
      </div>

      <!-- Features Comparison -->
      <section class="features-section">
        <h2>Comparativo completo</h2>
        
        <div class="features-table">
          <div class="table-header">
            <div class="feature-name">Recursos</div>
            <div class="plan-col">Free</div>
            <div class="plan-col">Basic</div>
            <div class="plan-col highlight">Pro</div>
            <div class="plan-col">Elite</div>
          </div>
          
          <div class="table-row">
            <div class="feature-name">Análises por dia</div>
            <div class="plan-col">3</div>
            <div class="plan-col">Ilimitado</div>
            <div class="plan-col highlight">Ilimitado</div>
            <div class="plan-col">Ilimitado</div>
          </div>
          
          <div class="table-row">
            <div class="feature-name">Histórico</div>
            <div class="plan-col">7 dias</div>
            <div class="plan-col">30 dias</div>
            <div class="plan-col highlight">90 dias</div>
            <div class="plan-col">Ilimitado</div>
          </div>
          
          <div class="table-row">
            <div class="feature-name">Dashboard</div>
            <div class="plan-col">Básico</div>
            <div class="plan-col">Completo</div>
            <div class="plan-col highlight">Completo</div>
            <div class="plan-col">Completo</div>
          </div>
          
          <div class="table-row">
            <div class="feature-name">IA Avançada</div>
            <div class="plan-col">—</div>
            <div class="plan-col">—</div>
            <div class="plan-col highlight">✓</div>
            <div class="plan-col">✓</div>
          </div>
          
          <div class="table-row">
            <div class="feature-name">Alertas em tempo real</div>
            <div class="plan-col">—</div>
            <div class="plan-col">—</div>
            <div class="plan-col highlight">✓</div>
            <div class="plan-col">✓</div>
          </div>
          
          <div class="table-row">
            <div class="feature-name">Paper Trading</div>
            <div class="plan-col">—</div>
            <div class="plan-col">—</div>
            <div class="plan-col highlight">✓</div>
            <div class="plan-col">✓</div>
          </div>
          
          <div class="table-row">
            <div class="feature-name">Cartola FC</div>
            <div class="plan-col">—</div>
            <div class="plan-col">—</div>
            <div class="plan-col highlight">✓</div>
            <div class="plan-col">✓</div>
          </div>
          
          <div class="table-row">
            <div class="feature-name">API Access</div>
            <div class="plan-col">—</div>
            <div class="plan-col">—</div>
            <div class="plan-col highlight">—</div>
            <div class="plan-col">✓</div>
          </div>
          
          <div class="table-row">
            <div class="feature-name">Webhooks</div>
            <div class="plan-col">—</div>
            <div class="plan-col">—</div>
            <div class="plan-col highlight">—</div>
            <div class="plan-col">✓</div>
          </div>
          
          <div class="table-row">
            <div class="feature-name">Suporte</div>
            <div class="plan-col">Email</div>
            <div class="plan-col">Email</div>
            <div class="plan-col highlight">Prioritário</div>
            <div class="plan-col">24/7</div>
          </div>
        </div>
      </section>

      <!-- FAQ -->
      <section class="faq-section">
        <h2>Perguntas frequentes</h2>
        
        <div class="faq-grid">
          <div class="faq-item">
            <h4>Posso cancelar a qualquer momento?</h4>
            <p>Sim! Você pode cancelar sua assinatura a qualquer momento. O acesso continua até o fim do período pago.</p>
          </div>
          <div class="faq-item">
            <h4>Como funciona o período de teste?</h4>
            <p>O plano Free é permanente e gratuito. Você pode usar para sempre com as limitações do plano.</p>
          </div>
          <div class="faq-item">
            <h4>Quais formas de pagamento?</h4>
            <p>Aceitamos cartões de crédito (Visa, Mastercard, Amex) e boleto bancário para planos anuais.</p>
          </div>
          <div class="faq-item">
            <h4>Posso trocar de plano?</h4>
            <p>Sim! Você pode fazer upgrade ou downgrade a qualquer momento. O valor é calculado proporcionalmente.</p>
          </div>
        </div>
      </section>

      <!-- CTA -->
      <section class="cta-section">
        <h2>Ainda tem dúvidas?</h2>
        <p>Fale com nosso time de suporte</p>
        <a href="mailto:suporte@odinenx.com" class="cta-btn">Entrar em contato</a>
      </section>
    </main>

    <!-- Footer -->
    <footer class="pricing-footer">
      <p>© 2026 ODINENX. Todos os direitos reservados.</p>
      <div class="footer-links">
        <a href="#">Termos</a>
        <a href="#">Privacidade</a>
        <a href="#">Suporte</a>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.pricing-page {
  min-height: 100vh;
  background: #000;
  color: #fff;
}

/* Header */
.pricing-header {
  padding: 20px 40px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.header-logo {
  height: 40px;
}

.back-link {
  display: inline-block;
}

/* Main */
.pricing-main {
  max-width: 1400px;
  margin: 0 auto;
  padding: 60px 20px;
}

/* Hero */
.pricing-hero {
  text-align: center;
  margin-bottom: 60px;
}

.pricing-hero h1 {
  font-size: clamp(2.5rem, 5vw, 4rem);
  font-weight: 800;
  margin-bottom: 15px;
  letter-spacing: -1px;
}

.gradient-text {
  background: linear-gradient(90deg, #fff 0%, #888 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.pricing-hero > p {
  color: rgba(255, 255, 255, 0.6);
  font-size: 1.2rem;
  margin-bottom: 30px;
}

/* Billing Toggle */
.billing-toggle {
  display: inline-flex;
  align-items: center;
  gap: 15px;
  background: rgba(255, 255, 255, 0.05);
  padding: 8px 20px;
  border-radius: 50px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.billing-toggle span {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.95rem;
  transition: color 0.3s;
}

.billing-toggle span.active {
  color: #fff;
  font-weight: 600;
}

.discount-badge {
  background: #00ff88;
  color: #000;
  font-size: 0.7rem;
  padding: 2px 8px;
  border-radius: 10px;
  margin-left: 5px;
  font-weight: 700;
}

.toggle-btn {
  width: 50px;
  height: 26px;
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 20px;
  cursor: pointer;
  position: relative;
  transition: background 0.3s;
}

.toggle-btn.annual {
  background: #fff;
}

.toggle-indicator {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 20px;
  height: 20px;
  background: #fff;
  border-radius: 50%;
  transition: transform 0.3s;
}

.toggle-btn.annual .toggle-indicator {
  transform: translateX(24px);
  background: #000;
}

/* Error */
.error-banner {
  background: rgba(255, 107, 107, 0.1);
  border: 1px solid rgba(255, 107, 107, 0.3);
  color: #ff6b6b;
  padding: 15px 20px;
  border-radius: 10px;
  text-align: center;
  margin-bottom: 30px;
}

/* Plans Grid */
.plans-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 100px;
}

.plan-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 35px 25px;
  position: relative;
  transition: all 0.3s;
}

.plan-card:hover {
  transform: translateY(-5px);
  border-color: rgba(255, 255, 255, 0.2);
}

.plan-card.popular {
  background: #fff;
  color: #000;
  transform: scale(1.05);
}

.plan-card.popular:hover {
  transform: scale(1.05) translateY(-5px);
}

.plan-card.current {
  border-color: #00ff88;
}

.popular-badge,
.current-badge {
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  padding: 5px 15px;
  border-radius: 20px;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 1px;
}

.popular-badge {
  background: #000;
  color: #fff;
}

.current-badge {
  background: #00ff88;
  color: #000;
}

.plan-header {
  text-align: center;
  margin-bottom: 30px;
}

.plan-header h3 {
  font-size: 1.4rem;
  margin-bottom: 15px;
}

.plan-price {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 3px;
}

.currency {
  font-size: 1.2rem;
  font-weight: 600;
}

.amount {
  font-size: 3.5rem;
  font-weight: 800;
  line-height: 1;
}

.period {
  font-size: 1rem;
  opacity: 0.6;
}

.plan-billing {
  font-size: 0.85rem;
  opacity: 0.6;
  margin-top: 8px;
}

.plan-features {
  list-style: none;
  padding: 0;
  margin: 0 0 30px 0;
}

.plan-features li {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 0;
  font-size: 0.95rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.plan-card.popular .plan-features li {
  border-color: rgba(0, 0, 0, 0.1);
}

.check {
  color: #00ff88;
  font-weight: bold;
}

.plan-card.popular .check {
  color: #000;
}

.plan-btn {
  width: 100%;
  padding: 15px;
  border-radius: 10px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  background: transparent;
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.plan-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.1);
  border-color: #fff;
}

.plan-btn.primary {
  background: #000;
  color: #fff;
  border: none;
}

.plan-btn.primary:hover:not(:disabled) {
  opacity: 0.9;
  transform: translateY(-2px);
}

.plan-btn.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spinner {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Features Table */
.features-section {
  margin-bottom: 100px;
}

.features-section h2 {
  text-align: center;
  font-size: 2rem;
  margin-bottom: 40px;
}

.features-table {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  overflow: hidden;
}

.table-header,
.table-row {
  display: grid;
  grid-template-columns: 2fr repeat(4, 1fr);
  text-align: center;
}

.table-header {
  background: rgba(255, 255, 255, 0.05);
  font-weight: 600;
  padding: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.table-row {
  padding: 15px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.table-row:last-child {
  border-bottom: none;
}

.feature-name {
  text-align: left;
}

.plan-col {
  color: rgba(255, 255, 255, 0.7);
}

.plan-col.highlight {
  color: #fff;
  font-weight: 600;
}

/* FAQ */
.faq-section {
  margin-bottom: 100px;
}

.faq-section h2 {
  text-align: center;
  font-size: 2rem;
  margin-bottom: 40px;
}

.faq-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 30px;
}

.faq-item {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 15px;
  padding: 30px;
}

.faq-item h4 {
  font-size: 1.1rem;
  margin-bottom: 12px;
}

.faq-item p {
  color: rgba(255, 255, 255, 0.6);
  line-height: 1.6;
}

/* CTA */
.cta-section {
  text-align: center;
  padding: 60px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
}

.cta-section h2 {
  font-size: 2rem;
  margin-bottom: 10px;
}

.cta-section p {
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 25px;
}

.cta-btn {
  display: inline-block;
  padding: 15px 40px;
  background: #fff;
  color: #000;
  border-radius: 10px;
  font-weight: 600;
  transition: all 0.3s;
}

.cta-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(255, 255, 255, 0.2);
}

/* Footer */
.pricing-footer {
  padding: 40px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pricing-footer p {
  color: rgba(255, 255, 255, 0.5);
}

.footer-links {
  display: flex;
  gap: 30px;
}

.footer-links a {
  color: rgba(255, 255, 255, 0.5);
  transition: color 0.3s;
}

.footer-links a:hover {
  color: #fff;
}

/* Responsive */
@media (max-width: 1200px) {
  .plans-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .plan-card.popular {
    transform: none;
  }
}

@media (max-width: 968px) {
  .features-table {
    overflow-x: auto;
  }
  
  .table-header,
  .table-row {
    min-width: 700px;
  }
  
  .faq-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .pricing-header {
    padding: 15px 20px;
  }
  
  .pricing-main {
    padding: 40px 15px;
  }
  
  .plans-grid {
    grid-template-columns: 1fr;
  }
  
  .plan-card.popular {
    order: -1;
  }
  
  .pricing-footer {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
}

@media (max-width: 480px) {
  .billing-toggle {
    flex-wrap: wrap;
    justify-content: center;
    padding: 15px;
  }
  
  .cta-section {
    padding: 40px 20px;
  }
}
</style>
