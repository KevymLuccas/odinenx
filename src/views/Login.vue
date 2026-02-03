<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../lib/supabase'

const router = useRouter()
const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

const handleLogin = async () => {
  try {
    loading.value = true
    error.value = ''

    const { error: authError } = await supabase.auth.signInWithPassword({
      email: email.value,
      password: password.value
    })

    if (authError) throw authError

    router.push('/dashboard?login=success')
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-container">
      <router-link to="/" class="back-link">← Voltar</router-link>
      
      <div class="auth-header">
        <img src="/logo.webp" alt="ODINENX" class="auth-logo" />
        <h1>Entrar</h1>
        <p>Acesse sua conta ODINENX</p>
      </div>

      <form @submit.prevent="handleLogin" class="auth-form">
        <div class="form-group">
          <label for="email">Email</label>
          <input
            type="email"
            id="email"
            v-model="email"
            placeholder="seu@email.com"
            required
          />
        </div>

        <div class="form-group">
          <label for="password">Senha</label>
          <input
            type="password"
            id="password"
            v-model="password"
            placeholder="••••••••"
            required
          />
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <button type="submit" class="btn-submit" :disabled="loading">
          {{ loading ? 'Entrando...' : 'Entrar' }}
        </button>
      </form>

      <p class="auth-footer">
        Não tem conta? <router-link to="/register">Criar conta grátis</router-link>
      </p>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  min-height: 100dvh;
  min-height: -webkit-fill-available;
  background: #000;
  display: -webkit-box;
  display: -webkit-flex;
  display: flex;
  -webkit-box-pack: center;
  -webkit-justify-content: center;
  justify-content: center;
  -webkit-box-align: center;
  -webkit-align-items: center;
  align-items: center;
  padding: 20px;
  padding-top: calc(20px + env(safe-area-inset-top));
  padding-bottom: calc(20px + env(safe-area-inset-bottom));
  padding-left: calc(20px + env(safe-area-inset-left));
  padding-right: calc(20px + env(safe-area-inset-right));
}

.auth-container {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 40px;
  width: 100%;
  max-width: 420px;
  -webkit-transform: translateZ(0);
  transform: translateZ(0);
}

.back-link {
  color: rgba(255, 255, 255, 0.5);
  text-decoration: none;
  font-size: 0.9rem;
  -webkit-transition: color 0.3s;
  transition: color 0.3s;
  -webkit-tap-highlight-color: transparent;
}

.back-link:hover {
  color: #fff;
}

.auth-header {
  text-align: center;
  margin: 30px 0;
}

.auth-logo {
  max-width: 150px;
  margin-bottom: 25px;
}

.auth-header h1 {
  color: #fff;
  font-size: 2rem;
  margin-bottom: 8px;
  font-weight: 700;
}

.auth-header p {
  color: rgba(255, 255, 255, 0.5);
}

.auth-form {
  display: -webkit-box;
  display: -webkit-flex;
  display: flex;
  -webkit-box-orient: vertical;
  -webkit-box-direction: normal;
  -webkit-flex-direction: column;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: -webkit-box;
  display: -webkit-flex;
  display: flex;
  -webkit-box-orient: vertical;
  -webkit-box-direction: normal;
  -webkit-flex-direction: column;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  color: #fff;
  font-weight: 500;
  font-size: 0.9rem;
}

.form-group input {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 10px;
  padding: 15px;
  color: #fff;
  font-size: 16px; /* Previne zoom no iOS */
  -webkit-transition: all 0.3s;
  transition: all 0.3s;
  -webkit-appearance: none;
  appearance: none;
  -webkit-tap-highlight-color: transparent;
}

.form-group input:focus {
  outline: none;
  border-color: #fff;
  background: rgba(255, 255, 255, 0.08);
}

.form-group input::placeholder {
  color: rgba(255, 255, 255, 0.3);
}

.error-message {
  background: rgba(255, 107, 107, 0.1);
  border: 1px solid rgba(255, 107, 107, 0.3);
  color: #ff6b6b;
  padding: 12px;
  border-radius: 10px;
  font-size: 0.9rem;
}

.btn-submit {
  background: #fff;
  color: #000;
  padding: 15px;
  border: none;
  border-radius: 10px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  -webkit-transition: all 0.3s;
  transition: all 0.3s;
  -webkit-appearance: none;
  appearance: none;
  -webkit-tap-highlight-color: transparent;
}

.btn-submit:hover:not(:disabled) {
  -webkit-transform: translateY(-2px);
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(255, 255, 255, 0.2);
}

.btn-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.divider {
  display: -webkit-box;
  display: -webkit-flex;
  display: flex;
  -webkit-box-align: center;
  -webkit-align-items: center;
  align-items: center;
  margin: 25px 0;
}

.divider::before,
.divider::after {
  content: '';
  -webkit-box-flex: 1;
  -webkit-flex: 1;
  flex: 1;
  height: 1px;
  background: rgba(255, 255, 255, 0.1);
}

.divider span {
  padding: 0 15px;
  color: rgba(255, 255, 255, 0.4);
  font-size: 0.9rem;
}

.btn-google {
  display: -webkit-box;
  display: -webkit-flex;
  display: flex;
  -webkit-box-align: center;
  -webkit-align-items: center;
  align-items: center;
  -webkit-box-pack: center;
  -webkit-justify-content: center;
  justify-content: center;
  gap: 12px;
  width: 100%;
  padding: 15px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 10px;
  font-size: 1rem;
  font-weight: 500;
  color: #fff;
  cursor: pointer;
  -webkit-transition: all 0.3s;
  transition: all 0.3s;
  -webkit-tap-highlight-color: transparent;
}

.btn-google:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.3);
}

.btn-google:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.auth-footer {
  text-align: center;
  margin-top: 25px;
  color: rgba(255, 255, 255, 0.5);
}

.auth-footer a {
  color: #fff;
  text-decoration: none;
  font-weight: 600;
  -webkit-tap-highlight-color: transparent;
}

.auth-footer a:hover {
  text-decoration: underline;
}

/* Responsivo */
@media (max-width: 480px) {
  .auth-container {
    padding: 25px 20px;
    border-radius: 16px;
  }
  
  .auth-logo {
    max-width: 120px;
  }
  
  .auth-header h1 {
    font-size: 1.6rem;
  }
  
  .form-group input {
    padding: 14px;
    font-size: 16px; /* Mantém 16px para evitar zoom no iOS */
  }
  
  .btn-submit {
    padding: 14px;
  }
}
</style>
