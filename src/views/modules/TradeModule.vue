<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="module-trade">
    <div class="module-header">
      <button @click="router.push('/dashboard')" class="back-btn">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
        Voltar
      </button>
      <h1>Módulo TRADE</h1>
      <p>Análise de mercados financeiros com IA</p>
    </div>

    <div class="coming-soon">
      <div class="icon-wrapper">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/>
          <polyline points="16 7 22 7 22 13"/>
        </svg>
      </div>
      <h2>Em Desenvolvimento</h2>
      <p>O módulo TRADE está sendo construído com tecnologias avançadas de análise financeira.</p>
      <div class="features-preview">
        <div class="feature">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          <span>Análise técnica automatizada</span>
        </div>
        <div class="feature">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          <span>Indicadores em tempo real</span>
        </div>
        <div class="feature">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          <span>Sinais de entrada e saída</span>
        </div>
        <div class="feature">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          <span>Paper Trading integrado</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.module-trade {
  min-height: 100vh;
  background: #000;
  color: #fff;
  padding: 30px;
}

.module-header {
  margin-bottom: 50px;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.7);
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 30px;
}

.back-btn:hover {
  border-color: #fff;
  color: #fff;
}

.back-btn svg {
  width: 18px;
  height: 18px;
}

.module-header h1 {
  font-size: 2.5rem;
  font-weight: 800;
  margin-bottom: 10px;
}

.module-header p {
  color: rgba(255, 255, 255, 0.5);
  font-size: 1.1rem;
}

.coming-soon {
  max-width: 600px;
  margin: 0 auto;
  text-align: center;
  padding: 60px 40px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
}

.icon-wrapper {
  width: 100px;
  height: 100px;
  background: rgba(59, 130, 246, 0.15);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 30px;
}

.icon-wrapper svg {
  width: 50px;
  height: 50px;
  stroke: #3b82f6;
}

.coming-soon h2 {
  font-size: 1.8rem;
  margin-bottom: 15px;
}

.coming-soon > p {
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 40px;
}

.features-preview {
  text-align: left;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  padding: 25px;
}

.feature {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.feature:last-child {
  border-bottom: none;
}

.feature svg {
  width: 20px;
  height: 20px;
  stroke: #3b82f6;
  flex-shrink: 0;
}

.feature span {
  color: rgba(255, 255, 255, 0.8);
}
</style>
