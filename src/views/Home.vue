<script setup>
import { ref, onMounted } from 'vue'
import Navbar from '../components/Navbar.vue'

const animationComplete = ref(false)
const showContent = ref(false)

onMounted(() => {
  setTimeout(() => {
    animationComplete.value = true
  }, 1500)
  
  setTimeout(() => {
    showContent.value = true
  }, 2200)
})
</script>

<template>
  <div class="home">
    <!-- Logo Animada -->
    <div class="logo-container" :class="{ 'animate-up': animationComplete }">
      <img src="/logo.webp" alt="ODINENX" class="logo" />
      <div class="logo-tagline" :class="{ 'fade-out': animationComplete }">
        Inteligência que opera. Você decide.
      </div>
    </div>

    <!-- Navbar Flutuante -->
    <Navbar :visible="showContent" />

    <!-- Conteúdo Principal -->
    <main class="content" :class="{ 'visible': showContent }">
      <!-- Hero Section -->
      <section class="hero">
        <a href="https://fantomstore.com.br" target="_blank" rel="noopener" class="hero-badge">
          <img src="https://i.imgur.com/vNwaSEm.png" alt="Fantom Store" class="badge-logo" />
          <span>Uma solução da <strong>Fantom Store</strong></span>
        </a>
        <h1>Análises precisas para <br><span class="gradient-text">BET</span> e <span class="gradient-text">TRADE</span></h1>
        <p class="subtitle">
          Zero promessas vazias. Dados reais, cálculos precisos e transparência total.
          <br>Você decide, a ODINENX informa.
        </p>
        <div class="cta-buttons">
          <router-link to="/register" class="btn btn-primary">
            Começar Grátis
            <span class="btn-arrow">→</span>
          </router-link>
          <a href="#modules" class="btn btn-ghost">
            Ver Módulos
          </a>
        </div>
        
        <!-- Stats -->
        <div class="hero-stats">
          <div class="stat">
            <span class="stat-number">2</span>
            <span class="stat-label">Módulos Integrados</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat">
            <span class="stat-number">IA</span>
            <span class="stat-label">Análise Inteligente</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat">
            <span class="stat-number">Live</span>
            <span class="stat-label">Dados em Tempo Real</span>
          </div>
        </div>
      </section>

      <!-- Módulos Section -->
      <section id="modules" class="modules">
        <h2 class="section-title">Dois mundos. <span class="gradient-text">Uma inteligência.</span></h2>
        
        <div class="modules-grid">
          <!-- Módulo BET -->
          <div class="module-card bet">
            <div class="module-icon">⚽</div>
            <div class="module-badge">MÓDULO BET</div>
            <h3>Apostas Esportivas</h3>
            <p>Análises completas de futebol com IA que calcula probabilidades reais.</p>
            
            <ul class="module-features">
              <li>✓ Resultado final, Over/Under, BTTS</li>
              <li>✓ Escanteios e Cartões</li>
              <li>✓ Handicap Asiático</li>
              <li>✓ Histórico de confrontos</li>
              <li>✓ Desfalques e lesões</li>
            </ul>
            
            <div class="module-leagues">
              <span>🇧🇷 Brasileirão</span>
              <span>🏆 Libertadores</span>
              <span>🌍 Europeus</span>
            </div>
          </div>

          <!-- Módulo TRADE -->
          <div class="module-card trade">
            <div class="module-icon">📈</div>
            <div class="module-badge">MÓDULO TRADE</div>
            <h3>Mercado Financeiro</h3>
            <p>Sinais precisos com entrada, alvo e stop. Análise técnica automatizada.</p>
            
            <ul class="module-features">
              <li>✓ Mini Índice (WIN) e Mini Dólar (WDO)</li>
              <li>✓ Ações B3 e Criptomoedas</li>
              <li>✓ RSI, MACD, Médias Móveis</li>
              <li>✓ Leitura de Fluxo</li>
              <li>✓ Scanner de Oportunidades</li>
            </ul>
            
            <div class="module-markets">
              <span>📊 B3</span>
              <span>₿ Crypto</span>
              <span>💱 Forex</span>
            </div>
          </div>
        </div>
      </section>

      <!-- IA Section -->
      <section class="ia-section">
        <div class="ia-content">
          <div class="ia-text">
            <h2>Inteligência Artificial <span class="gradient-text">de verdade</span></h2>
            <p>Não é achismo. É matemática, estatística e machine learning trabalhando juntos.</p>
            
            <div class="ia-features">
              <div class="ia-feature">
                <div class="ia-feature-icon">🎯</div>
                <div>
                  <h4>Probabilidade Real</h4>
                  <p>Cálculo preciso baseado em milhares de dados</p>
                </div>
              </div>
              <div class="ia-feature">
                <div class="ia-feature-icon">🔍</div>
                <div>
                  <h4>Identificação de Padrões</h4>
                  <p>A IA encontra o que o olho humano não vê</p>
                </div>
              </div>
              <div class="ia-feature">
                <div class="ia-feature-icon">📊</div>
                <div>
                  <h4>Backtesting</h4>
                  <p>Estratégias testadas em dados históricos</p>
                </div>
              </div>
              <div class="ia-feature">
                <div class="ia-feature-icon">⚡</div>
                <div>
                  <h4>Aprendizado Contínuo</h4>
                  <p>A IA evolui a cada operação</p>
                </div>
              </div>
            </div>
          </div>
          
          <div class="ia-visual">
            <div class="ia-card">
              <div class="ia-card-header">
                <span class="live-dot"></span>
                ANÁLISE AO VIVO
              </div>
              <div class="ia-card-body">
                <div class="analysis-item">
                  <span>Flamengo x Palmeiras</span>
                  <span class="confidence high">87% confiança</span>
                </div>
                <div class="analysis-result">
                  <span class="result-label">Over 2.5 Gols</span>
                  <span class="result-odd">@1.95</span>
                </div>
                <div class="analysis-bar">
                  <div class="bar-fill" style="width: 87%"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Preços Section -->
      <section id="pricing" class="pricing">
        <h2 class="section-title">Escolha seu <span class="gradient-text">plano</span></h2>
        <p class="section-subtitle">Comece grátis. Evolua quando quiser.</p>
        
        <div class="pricing-grid">
          <!-- Free -->
          <div class="price-card">
            <div class="price-header">
              <h3>Free</h3>
              <div class="price">
                <span class="currency">R$</span>
                <span class="amount">0</span>
                <span class="period">/mês</span>
              </div>
            </div>
            <ul class="price-features">
              <li>✓ 3 análises por dia</li>
              <li>✓ Dashboard básico</li>
              <li>✓ Histórico 7 dias</li>
              <li class="disabled">✗ Alertas</li>
              <li class="disabled">✗ API</li>
            </ul>
            <router-link to="/register" class="btn btn-outline">Começar Grátis</router-link>
          </div>

          <!-- Basic -->
          <div class="price-card">
            <div class="price-header">
              <h3>Basic</h3>
              <div class="price">
                <span class="currency">R$</span>
                <span class="amount">79</span>
                <span class="period">/mês</span>
              </div>
            </div>
            <ul class="price-features">
              <li>✓ Análises ilimitadas</li>
              <li>✓ Dashboard completo</li>
              <li>✓ Histórico 30 dias</li>
              <li>✓ Filtros de risco</li>
              <li class="disabled">✗ API</li>
            </ul>
            <router-link to="/register" class="btn btn-outline">Assinar Basic</router-link>
          </div>

          <!-- Pro -->
          <div class="price-card featured">
            <div class="price-badge">MAIS POPULAR</div>
            <div class="price-header">
              <h3>Pro</h3>
              <div class="price">
                <span class="currency">R$</span>
                <span class="amount">199</span>
                <span class="period">/mês</span>
              </div>
            </div>
            <ul class="price-features">
              <li>✓ Tudo do Basic</li>
              <li>✓ IA Completa</li>
              <li>✓ Alertas em tempo real</li>
              <li>✓ Paper Trading</li>
              <li>✓ Suporte prioritário</li>
            </ul>
            <router-link to="/register" class="btn btn-primary">Assinar Pro</router-link>
          </div>

          <!-- Elite -->
          <div class="price-card elite">
            <div class="price-header">
              <h3>Elite</h3>
              <div class="price">
                <span class="currency">R$</span>
                <span class="amount">399</span>
                <span class="period">/mês</span>
              </div>
            </div>
            <ul class="price-features">
              <li>✓ Tudo do Pro</li>
              <li>✓ Acesso à API</li>
              <li>✓ Webhooks</li>
              <li>✓ Suporte 24/7</li>
              <li>✓ Consultoria mensal</li>
            </ul>
            <router-link to="/register" class="btn btn-outline">Assinar Elite</router-link>
          </div>
        </div>
      </section>

      <!-- Filosofia -->
      <section class="philosophy">
        <div class="philosophy-content">
          <h2>Nossa <span class="gradient-text">filosofia</span></h2>
          <div class="philosophy-grid">
            <div class="philosophy-item">
              <span class="philosophy-icon">🚫</span>
              <h4>Zero promessas</h4>
              <p>Nunca prometemos resultado. Informamos probabilidades.</p>
            </div>
            <div class="philosophy-item">
              <span class="philosophy-icon">👁️</span>
              <h4>Transparência total</h4>
              <p>Taxa de acerto visível. Histórico aberto.</p>
            </div>
            <div class="philosophy-item">
              <span class="philosophy-icon">📐</span>
              <h4>Dados reais</h4>
              <p>Cálculos precisos, não achismos.</p>
            </div>
            <div class="philosophy-item">
              <span class="philosophy-icon">⚠️</span>
              <h4>Risco visível</h4>
              <p>Você sempre sabe o risco antes de decidir.</p>
            </div>
          </div>
        </div>
      </section>

      <!-- CTA Final -->
      <section class="cta-final">
        <h2>Pronto para operar com <span class="gradient-text">inteligência</span>?</h2>
        <p>Comece grátis agora. Sem cartão de crédito.</p>
        <router-link to="/register" class="btn btn-primary btn-large">
          Criar Conta Grátis
          <span class="btn-arrow">→</span>
        </router-link>
      </section>

      <!-- Footer -->
      <footer class="footer">
        <div class="footer-content">
          <div class="footer-brand">
            <img src="/logo.webp" alt="ODINENX" class="footer-logo" />
            <p>Inteligência que opera. Você decide.</p>
          </div>
          <div class="footer-links">
            <div class="footer-col">
              <h4>Produto</h4>
              <a href="#modules">Módulo BET</a>
              <a href="#modules">Módulo TRADE</a>
              <a href="#pricing">Preços</a>
            </div>
            <div class="footer-col">
              <h4>Suporte</h4>
              <a href="#">FAQ</a>
              <a href="#">Contato</a>
              <a href="#">Status</a>
            </div>
            <div class="footer-col">
              <h4>Legal</h4>
              <a href="#">Termos de Uso</a>
              <a href="#">Privacidade</a>
              <a href="#">Disclaimer</a>
            </div>
          </div>
        </div>
        <div class="footer-bottom">
          <p>© 2026 ODINENX. Todos os direitos reservados.</p>
          <p class="disclaimer">Investimentos e apostas envolvem riscos. Resultados passados não garantem resultados futuros.</p>
          
          <div class="fantom-brand">
            <a href="https://fantomstore.com.br" target="_blank" rel="noopener">
              <img src="https://i.imgur.com/vNwaSEm.png" alt="Fantom Store" class="fantom-logo" />
              <span>Uma solução da <strong>Fantom Store</strong></span>
            </a>
          </div>
        </div>
      </footer>
    </main>
  </div>
</template>

<style scoped>
.home {
  min-height: 100vh;
  background: #000;
  color: #fff;
  overflow-x: hidden;
}

/* Logo Container */
.logo-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 100;
  background: #000;
  transition: all 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

.logo-container.animate-up {
  height: 85px;
  background: rgba(0, 0, 0, 0.95);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding: 12px 20px;
  overflow: visible;
  justify-content: center;
  align-items: center;
}

.logo {
  max-width: 450px;
  width: 80%;
  transition: all 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  object-fit: contain;
}

.logo-container.animate-up .logo {
  max-width: 180px;
  width: auto;
  height: 58px;
  object-fit: contain;
  margin: 0;
}

.logo-tagline {
  margin-top: 20px;
  font-size: 1.2rem;
  color: rgba(255, 255, 255, 0.6);
  letter-spacing: 2px;
  text-transform: uppercase;
  transition: all 0.5s ease;
}

.logo-tagline.fade-out {
  opacity: 0;
  transform: translateY(-20px);
}

/* Gradient Text */
.gradient-text {
  background: linear-gradient(90deg, #fff 0%, #888 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Content */
.content {
  padding-top: 100px;
  opacity: 0;
  transform: translateY(30px);
  transition: all 0.6s ease-out;
}

.content.visible {
  opacity: 1;
  transform: translateY(0);
}

/* Hero */
.hero {
  text-align: center;
  padding: 100px 20px;
  min-height: 80vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.15);
  padding: 10px 22px;
  border-radius: 50px;
  font-size: 0.85rem;
  margin-bottom: 30px;
  text-decoration: none;
  color: rgba(255, 255, 255, 0.7);
  transition: all 0.3s ease;
}

.hero-badge:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.3);
  color: #fff;
}

.badge-logo {
  height: 22px;
  width: auto;
  opacity: 0.8;
}

.hero-badge:hover .badge-logo {
  opacity: 1;
}

.hero-badge strong {
  color: #fff;
}

.hero h1 {
  font-size: clamp(2.5rem, 6vw, 5rem);
  font-weight: 800;
  line-height: 1.1;
  margin-bottom: 25px;
  letter-spacing: -2px;
}

.subtitle {
  font-size: clamp(1rem, 2vw, 1.3rem);
  color: rgba(255, 255, 255, 0.6);
  max-width: 600px;
  margin-bottom: 40px;
  line-height: 1.7;
}

/* Buttons */
.cta-buttons {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
  justify-content: center;
  margin-bottom: 60px;
}

.btn {
  padding: 16px 32px;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.3s ease;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  border: none;
}

.btn-primary {
  background: #fff;
  color: #000;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 40px rgba(255, 255, 255, 0.2);
}

.btn-ghost {
  background: transparent;
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.btn-ghost:hover {
  border-color: #fff;
}

.btn-outline {
  background: transparent;
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.3);
  width: 100%;
  justify-content: center;
}

.btn-outline:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: #fff;
}

.btn-large {
  padding: 20px 50px;
  font-size: 1.1rem;
}

.btn-arrow {
  transition: transform 0.3s ease;
}

.btn:hover .btn-arrow {
  transform: translateX(5px);
}

/* Hero Stats */
.hero-stats {
  display: flex;
  align-items: center;
  gap: 40px;
  flex-wrap: wrap;
  justify-content: center;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-number {
  font-size: 2.5rem;
  font-weight: 800;
}

.stat-label {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.stat-divider {
  width: 1px;
  height: 40px;
  background: rgba(255, 255, 255, 0.2);
}

/* Section Titles */
.section-title {
  font-size: clamp(2rem, 4vw, 3rem);
  font-weight: 800;
  text-align: center;
  margin-bottom: 20px;
  letter-spacing: -1px;
}

.section-subtitle {
  text-align: center;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 60px;
}

/* Modules */
.modules {
  padding: 100px 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.modules-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 30px;
  margin-top: 60px;
}

.module-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 40px;
  transition: all 0.3s ease;
}

.module-card:hover {
  transform: translateY(-5px);
  border-color: rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.05);
}

.module-icon {
  font-size: 3rem;
  margin-bottom: 20px;
}

.module-badge {
  display: inline-block;
  background: rgba(255, 255, 255, 0.1);
  padding: 5px 15px;
  border-radius: 20px;
  font-size: 0.75rem;
  letter-spacing: 2px;
  margin-bottom: 15px;
}

.module-card h3 {
  font-size: 1.8rem;
  margin-bottom: 15px;
}

.module-card > p {
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 25px;
}

.module-features {
  list-style: none;
  padding: 0;
  margin: 0 0 25px 0;
}

.module-features li {
  padding: 8px 0;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.95rem;
}

.module-leagues,
.module-markets {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.module-leagues span,
.module-markets span {
  background: rgba(255, 255, 255, 0.1);
  padding: 8px 15px;
  border-radius: 20px;
  font-size: 0.85rem;
}

/* IA Section */
.ia-section {
  padding: 100px 20px;
  background: linear-gradient(180deg, transparent 0%, rgba(255, 255, 255, 0.02) 50%, transparent 100%);
}

.ia-content {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 60px;
  align-items: center;
}

.ia-text h2 {
  font-size: clamp(2rem, 4vw, 3rem);
  margin-bottom: 20px;
}

.ia-text > p {
  color: rgba(255, 255, 255, 0.6);
  font-size: 1.1rem;
  margin-bottom: 40px;
}

.ia-features {
  display: flex;
  flex-direction: column;
  gap: 25px;
}

.ia-feature {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.ia-feature-icon {
  font-size: 1.5rem;
  background: rgba(255, 255, 255, 0.1);
  padding: 15px;
  border-radius: 12px;
}

.ia-feature h4 {
  font-size: 1.1rem;
  margin-bottom: 5px;
}

.ia-feature p {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.9rem;
}

/* IA Visual Card */
.ia-visual {
  display: flex;
  justify-content: center;
}

.ia-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 30px;
  width: 100%;
  max-width: 400px;
}

.ia-card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.8rem;
  letter-spacing: 2px;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 25px;
}

.live-dot {
  width: 8px;
  height: 8px;
  background: #00ff88;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.ia-card-body {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.analysis-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.confidence {
  font-size: 0.85rem;
  padding: 5px 12px;
  border-radius: 20px;
}

.confidence.high {
  background: rgba(0, 255, 136, 0.2);
  color: #00ff88;
}

.analysis-result {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.05);
  padding: 15px 20px;
  border-radius: 10px;
}

.result-label {
  font-weight: 600;
}

.result-odd {
  color: #00ff88;
  font-weight: 700;
}

.analysis-bar {
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #fff, #888);
  border-radius: 10px;
  transition: width 1s ease;
}

/* Pricing */
.pricing {
  padding: 100px 20px;
  max-width: 1300px;
  margin: 0 auto;
}

.pricing-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.price-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 35px 30px;
  position: relative;
  transition: all 0.3s ease;
}

.price-card:hover {
  transform: translateY(-5px);
  border-color: rgba(255, 255, 255, 0.3);
}

.price-card.featured {
  background: #fff;
  color: #000;
  transform: scale(1.05);
}

.price-card.featured:hover {
  transform: scale(1.05) translateY(-5px);
}

.price-card.featured .btn-primary {
  background: #000;
  color: #fff;
}

.price-card.featured .price-features li.disabled {
  color: rgba(0, 0, 0, 0.3);
}

.price-badge {
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  background: #000;
  color: #fff;
  padding: 5px 20px;
  border-radius: 20px;
  font-size: 0.7rem;
  letter-spacing: 1px;
}

.price-header {
  text-align: center;
  margin-bottom: 30px;
}

.price-header h3 {
  font-size: 1.5rem;
  margin-bottom: 15px;
}

.price {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 5px;
}

.currency {
  font-size: 1.2rem;
}

.amount {
  font-size: 3.5rem;
  font-weight: 800;
  line-height: 1;
}

.period {
  color: rgba(255, 255, 255, 0.5);
}

.price-card.featured .period {
  color: rgba(0, 0, 0, 0.5);
}

.price-features {
  list-style: none;
  padding: 0;
  margin: 0 0 30px 0;
}

.price-features li {
  padding: 10px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.price-card.featured .price-features li {
  border-color: rgba(0, 0, 0, 0.1);
}

.price-features li.disabled {
  color: rgba(255, 255, 255, 0.3);
}

/* Philosophy */
.philosophy {
  padding: 100px 20px;
  background: rgba(255, 255, 255, 0.02);
}

.philosophy-content {
  max-width: 1000px;
  margin: 0 auto;
  text-align: center;
}

.philosophy h2 {
  font-size: clamp(2rem, 4vw, 3rem);
  margin-bottom: 60px;
}

.philosophy-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 40px;
}

.philosophy-item {
  text-align: center;
}

.philosophy-icon {
  font-size: 2.5rem;
  margin-bottom: 20px;
  display: block;
}

.philosophy-item h4 {
  font-size: 1.2rem;
  margin-bottom: 10px;
}

.philosophy-item p {
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.95rem;
}

/* CTA Final */
.cta-final {
  text-align: center;
  padding: 120px 20px;
}

.cta-final h2 {
  font-size: clamp(2rem, 4vw, 3rem);
  margin-bottom: 20px;
}

.cta-final p {
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 40px;
}

/* Footer */
.footer {
  padding: 80px 20px 40px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.footer-content {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 2fr 3fr;
  gap: 60px;
  margin-bottom: 60px;
}

.footer-logo {
  height: 40px;
  margin-bottom: 15px;
}

.footer-brand p {
  color: rgba(255, 255, 255, 0.5);
}

.footer-links {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 40px;
}

.footer-col h4 {
  margin-bottom: 20px;
  font-size: 0.9rem;
  letter-spacing: 1px;
}

.footer-col a {
  display: block;
  color: rgba(255, 255, 255, 0.5);
  padding: 8px 0;
  transition: color 0.3s;
}

.footer-col a:hover {
  color: #fff;
}

.footer-bottom {
  text-align: center;
  padding-top: 40px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.footer-bottom p {
  color: rgba(255, 255, 255, 0.4);
  font-size: 0.9rem;
}

.disclaimer {
  margin-top: 10px;
  font-size: 0.8rem !important;
}

.fantom-brand {
  margin-top: 30px;
  padding-top: 25px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.fantom-brand a {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
  color: rgba(255, 255, 255, 0.5);
  transition: all 0.3s ease;
  padding: 10px 20px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.02);
}

.fantom-brand a:hover {
  color: rgba(255, 255, 255, 0.8);
  background: rgba(255, 255, 255, 0.05);
}

.fantom-logo {
  height: 28px;
  width: auto;
  opacity: 0.7;
  transition: opacity 0.3s;
}

.fantom-brand a:hover .fantom-logo {
  opacity: 1;
}

.fantom-brand span {
  font-size: 0.85rem;
}

.fantom-brand strong {
  color: #fff;
}

/* Responsivo */
@media (max-width: 968px) {
  .ia-content {
    grid-template-columns: 1fr;
  }
  
  .footer-content {
    grid-template-columns: 1fr;
  }
  
  .footer-links {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .logo-container.animate-up {
    height: 70px;
    padding: 8px 15px;
  }
  
  .logo-container.animate-up .logo {
    max-width: 140px;
    height: 50px;
    margin: 0;
  }
  
  .hero {
    padding: 60px 20px;
  }
  
  .hero-stats {
    flex-direction: column;
    gap: 30px;
  }
  
  .stat-divider {
    width: 60px;
    height: 1px;
  }
  
  .modules-grid {
    grid-template-columns: 1fr;
  }
  
  .pricing-grid {
    grid-template-columns: 1fr;
  }
  
  .price-card.featured {
    transform: none;
  }
  
  .price-card.featured:hover {
    transform: translateY(-5px);
  }
  
  .footer-links {
    grid-template-columns: 1fr;
    text-align: center;
  }
}

@media (max-width: 480px) {
  .logo-container.animate-up {
    height: 55px;
  }
  
  .logo-container.animate-up .logo {
    max-width: 85px;
    height: 32px;
  }
  
  .logo {
    max-width: 280px;
  }
}
</style>
