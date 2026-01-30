<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { supabase } from '../lib/supabase'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const subscription = ref(null)

onMounted(async () => {
  // Aguarda um pouco para o webhook processar
  await new Promise(resolve => setTimeout(resolve, 2000))
  
  try {
    const { data: { user } } = await supabase.auth.getUser()
    
    if (user) {
      const { data } = await supabase
        .from('subscriptions')
        .select('*')
        .eq('user_id', user.id)
        .eq('status', 'active')
        .single()
      
      subscription.value = data
    }
  } catch (error) {
    console.error('Erro ao carregar assinatura:', error)
  } finally {
    loading.value = false
  }
})

const goToDashboard = () => {
  router.push('/dashboard')
}
</script>

<template>
  <div class="success-page">
    <div class="success-container">
      <!-- Loading -->
      <div v-if="loading" class="loading-state">
        <div class="spinner-large"></div>
        <p>Processando seu pagamento...</p>
      </div>

      <!-- Success -->
      <div v-else class="success-content">
        <div class="success-icon">✓</div>
        <h1>Pagamento confirmado!</h1>
        <p class="success-message">
          Sua assinatura foi ativada com sucesso. Você já pode aproveitar todos os recursos do seu plano.
        </p>
        
        <div v-if="subscription" class="plan-info">
          <div class="plan-badge">{{ subscription.plan?.toUpperCase() }}</div>
          <p>Próxima cobrança em {{ new Date(subscription.current_period_end).toLocaleDateString('pt-BR') }}</p>
        </div>

        <div class="success-actions">
          <button @click="goToDashboard" class="btn-primary">
            Ir para o Dashboard
            <span>→</span>
          </button>
          <router-link to="/" class="btn-secondary">
            Voltar ao início
          </router-link>
        </div>

        <div class="success-note">
          <p>📧 Enviamos um email de confirmação para você.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.success-page {
  min-height: 100vh;
  background: #000;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
}

.success-container {
  max-width: 500px;
  width: 100%;
  text-align: center;
}

/* Loading */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.spinner-large {
  width: 50px;
  height: 50px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-state p {
  color: rgba(255, 255, 255, 0.6);
}

/* Success */
.success-content {
  animation: fadeIn 0.5s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.success-icon {
  width: 80px;
  height: 80px;
  background: #00ff88;
  color: #000;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.5rem;
  font-weight: bold;
  margin: 0 auto 30px;
}

.success-content h1 {
  font-size: 2.5rem;
  font-weight: 800;
  margin-bottom: 15px;
  color: #fff;
}

.success-message {
  color: rgba(255, 255, 255, 0.6);
  font-size: 1.1rem;
  line-height: 1.6;
  margin-bottom: 30px;
}

/* Plan Info */
.plan-info {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 15px;
  padding: 25px;
  margin-bottom: 30px;
}

.plan-badge {
  display: inline-block;
  background: #fff;
  color: #000;
  padding: 8px 20px;
  border-radius: 20px;
  font-weight: 700;
  font-size: 0.9rem;
  letter-spacing: 1px;
  margin-bottom: 10px;
}

.plan-info p {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.9rem;
}

/* Actions */
.success-actions {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 30px;
}

.btn-primary {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
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

/* Note */
.success-note {
  padding: 20px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 10px;
}

.success-note p {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.9rem;
  margin: 0;
}

/* Responsive */
@media (max-width: 480px) {
  .success-content h1 {
    font-size: 2rem;
  }
  
  .success-icon {
    width: 60px;
    height: 60px;
    font-size: 2rem;
  }
}
</style>
