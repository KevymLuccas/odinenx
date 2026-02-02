<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../lib/supabase'

const router = useRouter()
const name = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const error = ref('')
const success = ref(false)

const handleRegister = async () => {
  try {
    loading.value = true
    error.value = ''

    if (password.value !== confirmPassword.value) {
      throw new Error('As senhas não coincidem')
    }

    if (password.value.length < 6) {
      throw new Error('A senha deve ter pelo menos 6 caracteres')
    }

    const { error: authError } = await supabase.auth.signUp({
      email: email.value,
      password: password.value,
      options: {
        data: {
          name: name.value
        }
      }
    })

    if (authError) throw authError

    success.value = true
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
        <h1>Criar Conta</h1>
        <p>Comece grátis. Sem cartão de crédito.</p>
      </div>

      <!-- Mensagem de Sucesso -->
      <div v-if="success" class="success-message">
        <div class="success-icon">✓</div>
        <h3>Conta criada!</h3>
        <p>Verifique seu email para confirmar.</p>
        <router-link to="/login" class="btn-submit">Ir para Login</router-link>
      </div>

      <!-- Formulário -->
      <form v-else @submit.prevent="handleRegister" class="auth-form">
        <div class="form-group">
          <label for="name">Nome</label>
          <input
            type="text"
            id="name"
            v-model="name"
            placeholder="Seu nome"
            required
          />
        </div>

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

        <div class="form-group">
          <label for="confirmPassword">Confirmar Senha</label>
          <input
            type="password"
            id="confirmPassword"
            v-model="confirmPassword"
            placeholder="••••••••"
            required
          />
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <button type="submit" class="btn-submit" :disabled="loading">
          {{ loading ? 'Criando...' : 'Criar Conta Grátis' }}
        </button>
      </form>

      <template v-if="!success">
        <p class="auth-footer">
          Já tem conta? <router-link to="/login">Fazer login</router-link>
        </p>
        
        <p class="terms">
          Ao criar conta, você concorda com os <a href="#">Termos de Uso</a> e <a href="#">Política de Privacidade</a>
        </p>
      </template>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  background: #000;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
}

.auth-container {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 40px;
  width: 100%;
  max-width: 420px;
}

.back-link {
  color: rgba(255, 255, 255, 0.5);
  text-decoration: none;
  font-size: 0.9rem;
  transition: color 0.3s;
}

.back-link:hover {
  color: #fff;
}

.auth-header {
  text-align: center;
  margin: 25px 0;
}

.auth-logo {
  max-width: 140px;
  margin-bottom: 20px;
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

.success-message {
  text-align: center;
  padding: 30px 0;
}

.success-icon {
  width: 60px;
  height: 60px;
  background: #fff;
  color: #000;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  margin: 0 auto 20px;
}

.success-message h3 {
  color: #fff;
  margin-bottom: 10px;
}

.success-message p {
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 25px;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.form-group {
  display: flex;
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
  padding: 14px;
  color: #fff;
  font-size: 1rem;
  transition: all 0.3s;
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
  transition: all 0.3s;
  text-decoration: none;
  text-align: center;
  display: block;
}

.btn-submit:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(255, 255, 255, 0.2);
}

.btn-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.divider {
  display: flex;
  align-items: center;
  margin: 22px 0;
}

.divider::before,
.divider::after {
  content: '';
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
  display: flex;
  align-items: center;
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
  transition: all 0.3s;
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
  margin-top: 22px;
  color: rgba(255, 255, 255, 0.5);
}

.auth-footer a {
  color: #fff;
  text-decoration: none;
  font-weight: 600;
}

.auth-footer a:hover {
  text-decoration: underline;
}

.terms {
  text-align: center;
  margin-top: 20px;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.4);
}

.terms a {
  color: rgba(255, 255, 255, 0.6);
  text-decoration: none;
}

.terms a:hover {
  color: #fff;
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
  }
  
  .btn-submit {
    padding: 14px;
  }
  
  .plan-cards {
    gap: 12px;
  }
}
</style>
