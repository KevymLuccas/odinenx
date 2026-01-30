<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../lib/supabase'

const router = useRouter()
const user = ref(null)
const saving = ref(false)

supabase.auth.getSession().then(({ data: { session } }) => {
  if (!session) {
    router.push('/login')
    return
  }
  user.value = session.user
})
</script>

<template>
  <div class="settings-page">
    <div class="page-header">
      <button @click="router.push('/dashboard')" class="back-btn">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
        Voltar
      </button>
      <h1>Configurações</h1>
      <p>Personalize sua experiência</p>
    </div>

    <div class="settings-grid">
      <div class="settings-card">
        <div class="card-header">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
            <circle cx="12" cy="7" r="4"/>
          </svg>
          <h3>Perfil</h3>
        </div>
        <div class="card-content">
          <div class="info-row">
            <span class="label">Nome</span>
            <span class="value">{{ user?.user_metadata?.name || 'Não informado' }}</span>
          </div>
          <div class="info-row">
            <span class="label">Email</span>
            <span class="value">{{ user?.email }}</span>
          </div>
        </div>
      </div>

      <div class="settings-card">
        <div class="card-header">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
          </svg>
          <h3>Notificações</h3>
        </div>
        <div class="card-content">
          <div class="toggle-row">
            <span>Alertas por email</span>
            <label class="toggle">
              <input type="checkbox" checked>
              <span class="slider"></span>
            </label>
          </div>
          <div class="toggle-row">
            <span>Alertas push</span>
            <label class="toggle">
              <input type="checkbox">
              <span class="slider"></span>
            </label>
          </div>
        </div>
      </div>

      <div class="settings-card">
        <div class="card-header">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
            <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
          </svg>
          <h3>Segurança</h3>
        </div>
        <div class="card-content">
          <button class="settings-btn">Alterar senha</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.settings-page {
  min-height: 100vh;
  background: #000;
  color: #fff;
  padding: 30px;
}

.page-header {
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

.page-header h1 {
  font-size: 2.5rem;
  font-weight: 800;
  margin-bottom: 10px;
}

.page-header p {
  color: rgba(255, 255, 255, 0.5);
  font-size: 1.1rem;
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 25px;
  max-width: 1200px;
}

.settings-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 15px;
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 25px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.card-header svg {
  width: 22px;
  height: 22px;
  stroke: #fff;
}

.card-header h3 {
  font-size: 1.1rem;
  font-weight: 600;
}

.card-content {
  padding: 25px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.info-row:last-child {
  border-bottom: none;
}

.label {
  color: rgba(255, 255, 255, 0.5);
}

.value {
  font-weight: 500;
}

.toggle-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.toggle-row:last-child {
  border-bottom: none;
}

.toggle {
  position: relative;
  width: 50px;
  height: 26px;
}

.toggle input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 26px;
  transition: 0.3s;
}

.slider:before {
  position: absolute;
  content: "";
  height: 20px;
  width: 20px;
  left: 3px;
  bottom: 3px;
  background: #fff;
  border-radius: 50%;
  transition: 0.3s;
}

.toggle input:checked + .slider {
  background: #22c55e;
}

.toggle input:checked + .slider:before {
  transform: translateX(24px);
}

.settings-btn {
  width: 100%;
  padding: 12px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.settings-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}
</style>
