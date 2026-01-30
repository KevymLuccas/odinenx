<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const goToPricing = () => {
  router.push('/pricing')
}
</script>

<template>
  <div class="cancel-page">
    <div class="cancel-container">
      <div class="cancel-icon">✕</div>
      <h1>Pagamento cancelado</h1>
      <p class="cancel-message">
        Seu pagamento foi cancelado. Não se preocupe, nenhuma cobrança foi realizada.
      </p>
      
      <div class="cancel-reasons">
        <h4>Teve algum problema?</h4>
        <ul>
          <li>💳 Problemas com o cartão? Tente outro método de pagamento</li>
          <li>❓ Dúvidas sobre os planos? <a href="mailto:suporte@odinenx.com">Fale conosco</a></li>
          <li>🎁 Precisa de um desconto? <a href="mailto:suporte@odinenx.com">Entre em contato</a></li>
        </ul>
      </div>

      <div class="cancel-actions">
        <button @click="goToPricing" class="btn-primary">
          Tentar novamente
        </button>
        <router-link to="/" class="btn-secondary">
          Voltar ao início
        </router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cancel-page {
  min-height: 100vh;
  background: #000;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
}

.cancel-container {
  max-width: 500px;
  width: 100%;
  text-align: center;
}

.cancel-icon {
  width: 80px;
  height: 80px;
  background: rgba(255, 107, 107, 0.2);
  color: #ff6b6b;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.5rem;
  font-weight: bold;
  margin: 0 auto 30px;
}

.cancel-container h1 {
  font-size: 2.5rem;
  font-weight: 800;
  margin-bottom: 15px;
  color: #fff;
}

.cancel-message {
  color: rgba(255, 255, 255, 0.6);
  font-size: 1.1rem;
  line-height: 1.6;
  margin-bottom: 40px;
}

.cancel-reasons {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 15px;
  padding: 30px;
  margin-bottom: 40px;
  text-align: left;
}

.cancel-reasons h4 {
  font-size: 1.1rem;
  margin-bottom: 20px;
  color: #fff;
}

.cancel-reasons ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.cancel-reasons li {
  padding: 12px 0;
  color: rgba(255, 255, 255, 0.7);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.cancel-reasons li:last-child {
  border-bottom: none;
}

.cancel-reasons a {
  color: #fff;
  text-decoration: underline;
}

.cancel-actions {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.btn-primary {
  padding: 18px 30px;
  background: #fff;
  color: #000;
  border: none;
  border-radius: 10px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(255, 255, 255, 0.2);
}

.btn-secondary {
  padding: 15px 30px;
  background: transparent;
  color: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  font-size: 1rem;
  transition: all 0.3s;
}

.btn-secondary:hover {
  color: #fff;
  border-color: rgba(255, 255, 255, 0.5);
}

@media (max-width: 480px) {
  .cancel-container h1 {
    font-size: 2rem;
  }
  
  .cancel-icon {
    width: 60px;
    height: 60px;
    font-size: 2rem;
  }
}
</style>
