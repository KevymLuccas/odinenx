<script setup>
import { ref, provide, onMounted } from 'vue'
import HelpWidget from './components/HelpWidget.vue'
import ToastNotification from './components/ToastNotification.vue'
import BetaBanner from './components/BetaBanner.vue'

// Toast global state
const toast = ref({
  show: false,
  type: 'success',
  title: '',
  message: ''
})

const showToast = (type, title, message, duration = 5000) => {
  toast.value = { show: true, type, title, message, duration }
}

const closeToast = () => {
  toast.value.show = false
}

// Provide toast function globally
provide('showToast', showToast)

// Check for login/register/payment success from URL params
onMounted(() => {
  const params = new URLSearchParams(window.location.search)
  
  if (params.get('login') === 'success') {
    showToast('welcome', 'Bem-vindo de volta! 👋', 'Bom te ver novamente. Confira os palpites do dia!')
    window.history.replaceState({}, '', window.location.pathname)
  }
  
  if (params.get('register') === 'success') {
    showToast('success', 'Conta criada com sucesso! 🎉', 'Seu trial de 3 dias começou. Aproveite todos os palpites!')
    window.history.replaceState({}, '', window.location.pathname)
  }
  
  if (params.get('payment') === 'success') {
    showToast('payment', 'Pagamento confirmado! 💳', 'Seu plano foi ativado. Acesso completo liberado!')
    window.history.replaceState({}, '', window.location.pathname)
  }
  
  if (params.get('upgrade') === 'success') {
    showToast('success', 'Upgrade realizado! 🚀', 'Agora você tem acesso a todos os recursos premium!')
    window.history.replaceState({}, '', window.location.pathname)
  }
})
</script>

<template>
  <BetaBanner />
  <router-view />
  <HelpWidget />
  <ToastNotification 
    :show="toast.show"
    :type="toast.type"
    :title="toast.title"
    :message="toast.message"
    :duration="toast.duration"
    @close="closeToast"
  />
</template>

<style scoped>
</style>
