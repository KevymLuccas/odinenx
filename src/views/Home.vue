<script setup>
import { ref, onMounted } from 'vue'
import { supabase } from '../lib/supabase'

const animationComplete = ref(false)
const showContent = ref(false)
const menuOpen = ref(false)
const user = ref(null)

onMounted(async () => {
  const { data: { session } } = await supabase.auth.getSession()
  user.value = session?.user ?? null
  
  setTimeout(() => {
    animationComplete.value = true
  }, 1800)
  
  setTimeout(() => {
    showContent.value = true
  }, 2500)
})

const toggleMenu = () => {
  menuOpen.value = !menuOpen.value
}

const logout = async () => {
  await supabase.auth.signOut()
  menuOpen.value = false
}
</script>

<template>
  <div class="home">
    <!-- Animação Inicial da Logo -->
    <div class="splash-screen" :class="{ 'hide': animationComplete }">
      <img src="/logo.webp" alt="ODINENX" class="splash-logo" />
      <div class="splash-tagline">Inteligência que opera. Você decide.</div>
      <div class="splash-loader">
        <div class="loader-bar"></div>
      </div>
    </div>

    <!-- Header Fixo -->
    <header class="main-header" :class="{ 'visible': animationComplete }">
      <div class="header-container">
        <router-link to="/" class="header-brand">
          <img src="/logo.webp" alt="ODINENX" class="header-logo" />
        </router-link>
        
        <nav class="header-nav desktop-nav">
          <a href="#modules" class="nav-link">Módulos</a>
          <a href="#pricing" class="nav-link">Preços</a>
          <a href="#about" class="nav-link">Sobre</a>
        </nav>
        
        <div class="header-actions desktop-nav">
          <template v-if="user">
            <router-link to="/dashboard" class="btn-dashboard">Dashboard</router-link>
          </template>
          <template v-else>
            <router-link to="/login" class="btn-login">Entrar</router-link>
            <router-link to="/register" class="btn-signup">Começar Grátis</router-link>
          </template>
        </div>
        
        <button class="mobile-toggle" @click="toggleMenu" aria-label="Menu">
          <span :class="{ 'open': menuOpen }"></span>
          <span :class="{ 'open': menuOpen }"></span>
          <span :class="{ 'open': menuOpen }"></span>
        </button>
      </div>
      
      <!-- Mobile Menu -->
      <div class="mobile-menu" :class="{ 'open': menuOpen }">
        <a href="#modules" class="nav-link" @click="menuOpen = false">Módulos</a>
        <a href="#pricing" class="nav-link" @click="menuOpen = false">Preços</a>
        <a href="#about" class="nav-link" @click="menuOpen = false">Sobre</a>
        <div class="mobile-divider"></div>
        <template v-if="user">
          <router-link to="/dashboard" class="btn-dashboard" @click="menuOpen = false">Dashboard</router-link>
          <button @click="logout" class="btn-logout-mobile">Sair</button>
        </template>
        <template v-else>
          <router-link to="/login" class="btn-login" @click="menuOpen = false">Entrar</router-link>
          <router-link to="/register" class="btn-signup" @click="menuOpen = false">Começar Grátis</router-link>
        </template>
      </div>
    </header>

    <!-- Conteúdo Principal -->
    <main class="content" :class="{ 'visible': showContent }">
      <!-- Hero Section -->
      <section class="hero">
        <div class="hero-glow"></div>
        <div class="hero-badge">
          <svg class="badge-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
          <span>Plataforma de <strong>Análise Inteligente</strong></span>
        </div>
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
            <div class="module-icon"><svg viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 2a10 10 0 0110 10M12 2a10 10 0 00-10 10M12 2v20M2 12h20" stroke="currentColor" stroke-width="1.5" fill="none"/></svg></div>
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
              <span><svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg> Brasileirão</span>
              <span><svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M19 5h-2V3H7v2H5c-1.1 0-2 .9-2 2v1c0 2.55 1.92 4.63 4.39 4.94.63 1.5 1.98 2.63 3.61 2.96V19H7v2h10v-2h-4v-3.1c1.63-.33 2.98-1.46 3.61-2.96C19.08 12.63 21 10.55 21 8V7c0-1.1-.9-2-2-2z"/></svg> Libertadores</span>
              <span><svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zm6.93 6h-2.95c-.32-1.25-.78-2.45-1.38-3.56 1.84.63 3.37 1.91 4.33 3.56zM12 4.04c.83 1.2 1.48 2.53 1.91 3.96h-3.82c.43-1.43 1.08-2.76 1.91-3.96zM4.26 14C4.1 13.36 4 12.69 4 12s.1-1.36.26-2h3.38c-.08.66-.14 1.32-.14 2 0 .68.06 1.34.14 2H4.26z"/></svg> Europeus</span>
            </div>
          </div>

          <!-- Módulo TRADE -->
          <div class="module-card trade">
            <div class="module-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22,7 13.5,15.5 8.5,10.5 2,17"/><polyline points="16,7 22,7 22,13"/></svg></div>
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
              <span><svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M5 9.2h3V19H5zM10.6 5h2.8v14h-2.8zm5.6 8H19v6h-2.8z"/></svg> B3</span>
              <span><svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M11.5 11.5v-2h1v2h2v1h-2v2h-1v-2h-2v-1h2zm.5-9C6.48 2.5 2.5 6.48 2.5 11.5S6.48 20.5 11.5 20.5h.5v-2h-.5c-3.86 0-7-3.14-7-7s3.14-7 7-7 7 3.14 7 7v.5h2v-.5c0-5.02-3.98-9-9-9z"/></svg> Crypto</span>
              <span><svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M12.89 11.1c-1.78-.59-2.64-.96-2.64-1.9 0-1.02 1.11-1.39 1.81-1.39 1.31 0 1.79.99 1.9 1.34l1.58-.67c-.15-.45-.82-1.92-2.54-2.24V5h-2v1.26c-2.48.56-2.49 2.86-2.49 2.96 0 2.27 2.25 2.91 3.35 3.31 1.58.56 2.28 1.07 2.28 2.03 0 1.13-1.05 1.61-1.98 1.61-1.82 0-2.34-1.87-2.4-2.09l-1.66.67c.63 2.19 2.28 2.78 2.9 2.96V19h2v-1.24c.4-.09 2.9-.59 2.9-3.22 0-1.39-.61-2.61-3.01-3.44z"/></svg> Forex</span>
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
                <div class="ia-feature-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg></div>
                <div>
                  <h4>Probabilidade Real</h4>
                  <p>Cálculo preciso baseado em milhares de dados</p>
                </div>
              </div>
              <div class="ia-feature">
                <div class="ia-feature-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg></div>
                <div>
                  <h4>Identificação de Padrões</h4>
                  <p>A IA encontra o que o olho humano não vê</p>
                </div>
              </div>
              <div class="ia-feature">
                <div class="ia-feature-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 20V10M12 20V4M6 20v-6"/></svg></div>
                <div>
                  <h4>Backtesting</h4>
                  <p>Estratégias testadas em dados históricos</p>
                </div>
              </div>
              <div class="ia-feature">
                <div class="ia-feature-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg></div>
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
              <span class="philosophy-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="m4.93 4.93 14.14 14.14"/></svg></span>
              <h4>Zero promessas</h4>
              <p>Nunca prometemos resultado. Informamos probabilidades.</p>
            </div>
            <div class="philosophy-item">
              <span class="philosophy-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg></span>
              <h4>Transparência total</h4>
              <p>Taxa de acerto visível. Histórico aberto.</p>
            </div>
            <div class="philosophy-item">
              <span class="philosophy-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg></span>
              <h4>Dados reais</h4>
              <p>Cálculos precisos, não achismos.</p>
            </div>
            <div class="philosophy-item">
              <span class="philosophy-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg></span>
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

/* ===== SPLASH SCREEN ===== */
.splash-screen {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 200;
  background: #000;
  transition: all 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

.splash-screen.hide {
  opacity: 0;
  visibility: hidden;
  pointer-events: none;
}

.splash-logo {
  max-width: 400px;
  width: 75%;
  animation: pulse-glow 2s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% { filter: drop-shadow(0 0 20px rgba(255,255,255,0.2)); }
  50% { filter: drop-shadow(0 0 40px rgba(255,255,255,0.4)); }
}

.splash-tagline {
  margin-top: 25px;
  font-size: 1.1rem;
  color: rgba(255, 255, 255, 0.5);
  letter-spacing: 3px;
  text-transform: uppercase;
}

.splash-loader {
  margin-top: 50px;
  width: 200px;
  height: 3px;
  background: rgba(255,255,255,0.1);
  border-radius: 10px;
  overflow: hidden;
}

.loader-bar {
  width: 0;
  height: 100%;
  background: linear-gradient(90deg, #fff, #888);
  border-radius: 10px;
  animation: load 1.8s ease-out forwards;
}

@keyframes load {
  0% { width: 0; }
  100% { width: 100%; }
}

/* ===== HEADER (NAVBAR FLUTUANTE) ===== */
.main-header {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%) translateY(-100px);
  width: calc(100% - 48px);
  max-width: 1200px;
  z-index: 100;
  background: rgba(10, 10, 10, 0.9);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  opacity: 0;
  transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.main-header.visible {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}

.header-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 16px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
}

.header-brand {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.header-logo {
  height: 38px;
  width: auto;
  transition: all 0.3s ease;
}

.header-logo:hover {
  filter: drop-shadow(0 0 10px rgba(255,255,255,0.3));
}

.header-nav {
  display: flex;
  align-items: center;
  gap: 35px;
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.nav-link {
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  font-size: 0.95rem;
  font-weight: 500;
  transition: all 0.3s ease;
  position: relative;
}

.nav-link::after {
  content: '';
  position: absolute;
  bottom: -5px;
  left: 0;
  width: 0;
  height: 2px;
  background: #fff;
  transition: width 0.3s ease;
}

.nav-link:hover {
  color: #fff;
}

.nav-link:hover::after {
  width: 100%;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.btn-login {
  color: rgba(255, 255, 255, 0.8);
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 500;
  padding: 10px 18px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.btn-login:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.btn-signup {
  background: #fff;
  color: #000;
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 600;
  padding: 10px 20px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.btn-signup:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(255, 255, 255, 0.2);
}

.btn-dashboard {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 500;
  padding: 10px 20px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
}

.btn-dashboard:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.4);
}

/* Mobile Toggle */
.mobile-toggle {
  display: none;
  flex-direction: column;
  gap: 5px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px;
}

.mobile-toggle span {
  width: 24px;
  height: 2px;
  background: #fff;
  transition: all 0.3s ease;
  border-radius: 2px;
}

.mobile-toggle span.open:nth-child(1) {
  transform: rotate(45deg) translate(5px, 5px);
}

.mobile-toggle span.open:nth-child(2) {
  opacity: 0;
}

.mobile-toggle span.open:nth-child(3) {
  transform: rotate(-45deg) translate(5px, -5px);
}

/* Mobile Menu */
.mobile-menu {
  display: none;
  flex-direction: column;
  gap: 8px;
  padding: 0 24px 20px;
  background: rgba(0, 0, 0, 0.95);
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.mobile-menu.open {
  display: flex;
}

.mobile-menu .nav-link {
  padding: 12px 0;
  font-size: 1rem;
}

.mobile-menu .nav-link::after {
  display: none;
}

.mobile-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.1);
  margin: 8px 0;
}

.mobile-menu .btn-signup,
.mobile-menu .btn-login,
.mobile-menu .btn-dashboard {
  text-align: center;
  margin-top: 5px;
}

.btn-logout-mobile {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.3);
  padding: 12px;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-logout-mobile:hover {
  background: rgba(239, 68, 68, 0.25);
}

/* Gradient Text */
.gradient-text {
  background: linear-gradient(135deg, #fff 0%, #888 50%, #fff 100%);
  background-size: 200% auto;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: shimmer 3s linear infinite;
}

@keyframes shimmer {
  0% { background-position: 0% center; }
  100% { background-position: 200% center; }
}

/* Content */
.content {
  padding-top: 100px;
  opacity: 0;
  transform: translateY(30px);
  transition: all 0.8s ease-out;
}

.content.visible {
  opacity: 1;
  transform: translateY(0);
}

/* Hero */
.hero {
  text-align: center;
  padding: 100px 24px 120px;
  min-height: calc(100vh - 80px);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  max-width: 1100px;
  margin: 0 auto;
  position: relative;
}

.hero-glow {
  position: absolute;
  top: 20%;
  left: 50%;
  transform: translateX(-50%);
  width: 600px;
  height: 400px;
  background: radial-gradient(ellipse, rgba(255,255,255,0.06) 0%, transparent 70%);
  pointer-events: none;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.12);
  padding: 10px 22px;
  border-radius: 50px;
  font-size: 0.85rem;
  margin-bottom: 35px;
  color: rgba(255, 255, 255, 0.7);
  transition: all 0.3s ease;
}

.hero-badge:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.25);
}

.badge-icon {
  width: 18px;
  height: 18px;
  color: rgba(255, 255, 255, 0.8);
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
  font-size: clamp(1.8rem, 4vw, 3rem);
  font-weight: 800;
  text-align: center;
  margin-bottom: 20px;
  letter-spacing: -1px;
  padding: 0 20px;
}

.section-subtitle {
  text-align: center;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 50px;
  padding: 0 20px;
}

/* Modules */
.modules {
  padding: 80px 20px;
  max-width: 1100px;
  margin: 0 auto;
  box-sizing: border-box;
}

.modules-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 25px;
  margin-top: 50px;
}

.module-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 35px 30px;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
}

.module-card:hover {
  transform: translateY(-5px);
  border-color: rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.05);
}

.module-icon {
  width: 60px;
  height: 60px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 16px;
}

.module-icon svg {
  width: 32px;
  height: 32px;
  color: #fff;
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
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.1);
  padding: 8px 15px;
  border-radius: 20px;
  font-size: 0.85rem;
}

.module-leagues span svg,
.module-markets span svg {
  flex-shrink: 0;
}

/* IA Section */
.ia-section {
  padding: 80px 20px;
  background: linear-gradient(180deg, transparent 0%, rgba(255, 255, 255, 0.02) 50%, transparent 100%);
}

.ia-content {
  max-width: 1100px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 50px;
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
  display: flex;
  align-items: center;
  justify-content: center;
  width: 50px;
  height: 50px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  flex-shrink: 0;
}

.ia-feature-icon svg {
  width: 24px;
  height: 24px;
  color: #fff;
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
  padding: 80px 20px;
  max-width: 1100px;
  margin: 0 auto;
  box-sizing: border-box;
}

.pricing-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  align-items: stretch;
}

.price-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 30px 24px;
  position: relative;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
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
  font-size: 1.3rem;
  margin-bottom: 12px;
}

.price {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 4px;
}

.currency {
  font-size: 1rem;
}

.amount {
  font-size: 2.8rem;
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
  margin: 0 0 25px 0;
  flex: 1;
}

.price-features li {
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  font-size: 0.9rem;
}

.price-card.featured .price-features li {
  border-color: rgba(0, 0, 0, 0.1);
}

.price-features li.disabled {
  color: rgba(255, 255, 255, 0.3);
}

/* Philosophy */
.philosophy {
  padding: 80px 20px;
  background: rgba(255, 255, 255, 0.02);
}

.philosophy-content {
  max-width: 1000px;
  margin: 0 auto;
  text-align: center;
}

.philosophy h2 {
  font-size: clamp(1.8rem, 4vw, 3rem);
  margin-bottom: 50px;
}

.philosophy-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 30px;
}

.philosophy-item {
  text-align: center;
}

.philosophy-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 60px;
  height: 60px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  margin: 0 auto 20px;
}

.philosophy-icon svg {
  width: 28px;
  height: 28px;
  color: #fff;
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
  padding: 100px 20px;
  max-width: 800px;
  margin: 0 auto;
}

.cta-final h2 {
  font-size: clamp(1.8rem, 4vw, 2.8rem);
  margin-bottom: 20px;
}

.cta-final p {
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 40px;
}

/* Footer */
.footer {
  padding: 60px 20px 40px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.footer-content {
  max-width: 1100px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 50px;
  margin-bottom: 50px;
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

/* Responsivo */
@media (max-width: 1024px) {
  .pricing-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
  }
  
  .philosophy-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 25px;
  }
  
  .modules-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  
  .ia-content {
    grid-template-columns: 1fr;
    gap: 40px;
  }
  
  .footer-content {
    grid-template-columns: 1fr;
    gap: 40px;
  }
}

@media (max-width: 768px) {
  .main-header {
    top: 12px;
    width: calc(100% - 24px);
    border-radius: 12px;
  }
  
  .content {
    padding-top: 90px;
  }
  
  .hero {
    padding: 50px 20px 70px;
    min-height: auto;
  }
  
  .hero h1 {
    font-size: clamp(1.8rem, 7vw, 2.5rem);
    letter-spacing: -1px;
  }
  
  .subtitle {
    font-size: 1rem;
    margin-bottom: 30px;
  }
  
  .cta-buttons {
    flex-direction: column;
    width: 100%;
    max-width: 300px;
    margin-bottom: 40px;
  }
  
  .btn {
    width: 100%;
    justify-content: center;
    padding: 14px 24px;
  }
  
  .hero-stats {
    flex-direction: column;
    gap: 25px;
  }
  
  .stat-divider {
    width: 60px;
    height: 1px;
  }
  
  .stat-number {
    font-size: 2rem;
  }
  
  .modules {
    padding: 60px 16px;
  }
  
  .modules-grid {
    grid-template-columns: 1fr;
  }
  
  .module-card {
    padding: 28px 24px;
  }
  
  .module-card h3 {
    font-size: 1.4rem;
  }
  
  .ia-section {
    padding: 60px 16px;
  }
  
  .ia-text h2 {
    font-size: clamp(1.6rem, 5vw, 2rem);
  }
  
  .ia-card {
    max-width: 100%;
    padding: 24px;
  }
  
  .pricing {
    padding: 60px 16px;
  }
  
  .pricing-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .price-card {
    padding: 28px 24px;
  }
  
  .price-card.featured {
    transform: none;
    order: -1;
  }
  
  .price-card.featured:hover {
    transform: translateY(-5px);
  }
  
  .amount {
    font-size: 2.5rem;
  }
  
  .philosophy {
    padding: 60px 16px;
  }
  
  .philosophy-grid {
    grid-template-columns: 1fr 1fr;
    gap: 20px;
  }
  
  .philosophy-icon {
    width: 50px;
    height: 50px;
  }
  
  .philosophy-icon svg {
    width: 22px;
    height: 22px;
  }
  
  .philosophy-item h4 {
    font-size: 1rem;
  }
  
  .philosophy-item p {
    font-size: 0.85rem;
  }
  
  .cta-final {
    padding: 70px 20px;
  }
  
  .cta-final h2 {
    font-size: clamp(1.5rem, 5vw, 2rem);
  }
  
  .btn-large {
    padding: 16px 32px;
    font-size: 1rem;
  }
  
  .footer {
    padding: 50px 16px 30px;
  }
  
  .footer-content {
    gap: 30px;
  }
  
  .footer-links {
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
  }
  
  .footer-col h4 {
    font-size: 0.8rem;
    margin-bottom: 12px;
  }
  
  .footer-col a {
    font-size: 0.85rem;
    padding: 6px 0;
  }
  
  .desktop-nav {
    display: none;
  }
  
  .mobile-toggle {
    display: flex;
  }
}

@media (max-width: 480px) {
  .main-header {
    top: 10px;
    width: calc(100% - 20px);
    border-radius: 10px;
  }
  
  .splash-logo {
    max-width: 280px;
  }
  
  .splash-tagline {
    font-size: 0.85rem;
    letter-spacing: 2px;
    padding: 0 20px;
    text-align: center;
  }
  
  .splash-loader {
    width: 150px;
  }
  
  .header-container {
    padding: 14px 16px;
  }
  
  .header-logo {
    height: 30px;
  }
  
  .content {
    padding-top: 80px;
  }
  
  .hero {
    padding: 50px 16px 70px;
  }
  
  .hero-badge {
    padding: 8px 16px;
    font-size: 0.75rem;
    margin-bottom: 20px;
  }
  
  .badge-icon {
    width: 14px;
    height: 14px;
  }
  
  .hero h1 {
    font-size: 1.8rem;
    margin-bottom: 18px;
  }
  
  .subtitle {
    font-size: 0.9rem;
  }
  
  .section-title {
    font-size: 1.5rem;
  }
  
  .philosophy-grid {
    grid-template-columns: 1fr;
    gap: 24px;
  }
  
  .footer-links {
    grid-template-columns: 1fr;
    text-align: center;
    gap: 25px;
  }
  
  .footer-brand {
    text-align: center;
  }
}
</style>
