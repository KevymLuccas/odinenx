<script setup>
import { ref, computed, onMounted, inject } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../lib/supabase'
import { getSubscriptionStatus, plans, isAdmin as checkIsAdmin } from '../lib/stripe'
import BottomNav from '../components/BottomNav.vue'

const router = useRouter()
const user = ref(null)
const subscription = ref(null)
const mobileMenuOpen = ref(false)
const saving = ref(false)
const userIsAdmin = ref(false)

// 📷 Avatar
const userAvatar = ref(null)
const showAvatarModal = ref(false)
const uploadingAvatar = ref(false)
const avatarInput = ref(null)

// Toast
const showToast = inject('showToast', () => {})

onMounted(async () => {
  const { data: { session } } = await supabase.auth.getSession()
  if (!session) { router.push('/login'); return }
  user.value = session.user
  subscription.value = await getSubscriptionStatus(session.user.id)
  userIsAdmin.value = await checkIsAdmin(session.user.id)
  
  // Carregar avatar
  await loadUserAvatar(session.user.id)
})

const currentPlan = computed(() => {
  const planId = subscription.value?.plan || 'free'
  return plans[planId] || plans.free
})

// 📷 Carregar avatar
async function loadUserAvatar(userId) {
  try {
    const { data } = await supabase
      .from('profiles')
      .select('avatar_url')
      .eq('id', userId)
      .single()
    
    if (data?.avatar_url) {
      userAvatar.value = data.avatar_url
    }
  } catch (err) {
    console.log('Avatar não disponível')
  }
}

// 📷 Upload de foto
async function handleAvatarUpload(event) {
  const file = event.target.files?.[0]
  if (!file) return
  
  if (file.size > 2 * 1024 * 1024) {
    showToast('error', 'Erro', 'A imagem deve ter no máximo 2MB')
    return
  }
  
  uploadingAvatar.value = true
  
  try {
    const fileExt = file.name.split('.').pop()
    const fileName = `${user.value.id}_${Date.now()}.${fileExt}`
    
    const { data: uploadData, error: uploadError } = await supabase.storage
      .from('avatars')
      .upload(fileName, file, { upsert: true })
    
    if (uploadError) throw uploadError
    
    const { data: { publicUrl } } = supabase.storage
      .from('avatars')
      .getPublicUrl(fileName)
    
    const { error: updateError } = await supabase
      .from('profiles')
      .upsert({ 
        id: user.value.id, 
        avatar_url: publicUrl,
        updated_at: new Date().toISOString()
      })
    
    if (updateError) throw updateError
    
    userAvatar.value = publicUrl
    showAvatarModal.value = false
    showToast('success', 'Foto atualizada!', 'Sua foto de perfil foi alterada.')
  } catch (err) {
    console.error('Erro ao fazer upload:', err)
    if (err.message?.includes('Bucket not found')) {
      showToast('error', 'Configuração pendente', 'O armazenamento ainda não foi configurado.')
    } else {
      showToast('error', 'Erro', 'Não foi possível atualizar a foto.')
    }
  } finally {
    uploadingAvatar.value = false
  }
}

const logout = async () => { await supabase.auth.signOut(); router.push('/') }
const toggleMobileMenu = () => { mobileMenuOpen.value = !mobileMenuOpen.value }
const navigateTo = (path) => { router.push(path); mobileMenuOpen.value = false }
</script>

<template>
  <div class="dashboard">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-header"><router-link to="/"><img src="/logo.webp" alt="ODINENX" class="sidebar-logo" /></router-link></div>
      <nav class="sidebar-nav">
        <div class="nav-category">Principal</div>
        <router-link to="/dashboard" class="nav-item"><svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>Dashboard</router-link>
        <div class="nav-category">Ao Vivo</div>
        <router-link to="/live" class="nav-item live-nav"><span class="live-indicator"></span><svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16 10 8"/></svg>Jogos ao Vivo</router-link>
        <div class="nav-category">Módulos</div>
        <router-link to="/bet" class="nav-item"><svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>BET</router-link>
        <router-link to="/trade" class="nav-item"><svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>TRADE</router-link>
        <router-link to="/cartola" class="nav-item"><svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/></svg>Cartola FC</router-link>
        <div class="nav-category">Acompanhamento</div>
        <router-link to="/alerts" class="nav-item"><svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>Alertas</router-link>
        <router-link to="/history" class="nav-item"><svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 8v4l3 3"/><circle cx="12" cy="12" r="10"/></svg>Histórico</router-link>
        <div class="nav-category">Sistema</div>
        <router-link to="/settings" class="nav-item active"><svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>Configurações</router-link>
      </nav>
      <div class="sidebar-footer">
        <div class="plan-badge-sidebar">{{ currentPlan.name }}</div>
        <button @click="logout" class="logout-btn"><svg class="logout-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>Sair</button>
      </div>
    </aside>

    <!-- Mobile Menu Button -->
    <button class="mobile-menu-btn" @click="toggleMobileMenu">
      <svg v-if="!mobileMenuOpen" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
      <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
    </button>

    <div v-if="mobileMenuOpen" class="mobile-overlay" @click="mobileMenuOpen = false"></div>
    <nav class="mobile-menu" :class="{ open: mobileMenuOpen }">
      <div class="mobile-menu-header"><img src="/logo.webp" alt="ODINENX" class="mobile-logo" /></div>
      <div class="mobile-nav">
        <button @click="navigateTo('/dashboard')" class="mobile-nav-item">Dashboard</button>
        <button @click="navigateTo('/live')" class="mobile-nav-item live-mobile">🔴 Ao Vivo</button>
        <button @click="navigateTo('/bet')" class="mobile-nav-item">BET</button>
        <button @click="navigateTo('/trade')" class="mobile-nav-item">TRADE</button>
        <button @click="navigateTo('/cartola')" class="mobile-nav-item">Cartola FC</button>
        <button @click="navigateTo('/alerts')" class="mobile-nav-item">Alertas</button>
        <button @click="navigateTo('/history')" class="mobile-nav-item">Histórico</button>
        <button @click="navigateTo('/settings')" class="mobile-nav-item active">Configurações</button>
      </div>
      <button @click="logout" class="mobile-logout">Sair</button>
    </nav>

    <!-- Main Content -->
    <main class="main-content">
      <header class="page-header"><h1>Configurações</h1><p>Personalize sua experiência</p></header>

      <div class="settings-grid">
        <!-- Card de Perfil com Foto -->
        <div class="settings-card profile-card">
          <div class="card-header">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            <h3>Perfil</h3>
          </div>
          <div class="card-content">
            <!-- Avatar Section -->
            <div class="avatar-section">
              <div class="avatar-wrapper" @click="showAvatarModal = true">
                <img v-if="userAvatar" :src="userAvatar" alt="Avatar" class="avatar-img" />
                <div v-else class="avatar-placeholder">
                  {{ (user?.user_metadata?.name || user?.email || 'U')[0].toUpperCase() }}
                </div>
                <span class="avatar-edit">📷</span>
              </div>
              <button class="btn-change-photo" @click="showAvatarModal = true">
                Alterar foto
              </button>
            </div>
            
            <div class="info-row"><span class="label">Nome</span><span class="value">{{ user?.user_metadata?.name || 'Não informado' }}</span></div>
            <div class="info-row"><span class="label">Email</span><span class="value">{{ user?.email }}</span></div>
            <div class="info-row">
              <span class="label">Plano</span>
              <span class="value plan-badge" :class="currentPlan.id">
                {{ currentPlan.badgeEmoji }} {{ currentPlan.name }}
              </span>
            </div>
          </div>
        </div>

        <!-- Card de Vantagens do Plano -->
        <div class="settings-card plan-card" :class="currentPlan.id">
          <div class="card-header">
            <span class="plan-emoji">{{ currentPlan.badgeEmoji || '🆓' }}</span>
            <h3>Seu Plano: {{ currentPlan.name }}</h3>
          </div>
          <div class="card-content">
            <div class="plan-price" v-if="currentPlan.price > 0">
              <span class="price-value">R$ {{ currentPlan.price.toFixed(2).replace('.', ',') }}</span>
              <span class="price-interval">/mês</span>
            </div>
            <div class="plan-price free" v-else>
              <span class="price-value">Grátis</span>
            </div>
            
            <ul class="plan-features">
              <li v-for="(feature, i) in currentPlan.features" :key="i">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                {{ feature }}
              </li>
            </ul>
            
            <router-link v-if="currentPlan.id === 'free'" to="/pricing" class="btn-upgrade">
              ⚡ Fazer Upgrade
            </router-link>
            <router-link v-else-if="currentPlan.id !== 'legend'" to="/pricing" class="btn-manage">
              🚀 Ver Outros Planos
            </router-link>
            <div v-else class="legend-badge">
              👑 Você tem o melhor plano!
            </div>
          </div>
        </div>

        <div class="settings-card">
          <div class="card-header">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
            <h3>Notificações</h3>
          </div>
          <div class="card-content">
            <div class="toggle-row"><span>Alertas por email</span><label class="toggle"><input type="checkbox" checked><span class="slider"></span></label></div>
            <div class="toggle-row"><span>Alertas push</span><label class="toggle"><input type="checkbox"><span class="slider"></span></label></div>
          </div>
        </div>

        <div class="settings-card">
          <div class="card-header">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
            <h3>Segurança</h3>
          </div>
          <div class="card-content"><button class="settings-btn">Alterar senha</button></div>
        </div>
      </div>
    </main>

    <!-- 📷 Modal de Upload de Avatar -->
    <div v-if="showAvatarModal" class="modal-overlay" @click.self="showAvatarModal = false">
      <div class="avatar-modal">
        <button class="modal-close" @click="showAvatarModal = false">&times;</button>
        <h3>📷 Alterar Foto de Perfil</h3>
        
        <div class="avatar-preview-container">
          <img v-if="userAvatar" :src="userAvatar" alt="Preview" class="avatar-preview" />
          <div v-else class="avatar-preview-placeholder">
            {{ (user?.user_metadata?.name || user?.email || 'U')[0].toUpperCase() }}
          </div>
        </div>
        
        <input 
          ref="avatarInput"
          type="file" 
          accept="image/png,image/jpeg,image/webp"
          @change="handleAvatarUpload"
          style="display: none"
        />
        
        <div class="avatar-modal-actions">
          <button 
            class="btn-upload-avatar" 
            @click="avatarInput?.click()"
            :disabled="uploadingAvatar"
          >
            {{ uploadingAvatar ? 'Enviando...' : '📤 Escolher Imagem' }}
          </button>
          <p class="avatar-hint">PNG, JPG ou WEBP - Máx. 2MB</p>
        </div>
      </div>
    </div>

    <!-- Bottom Navigation Mobile -->
    <BottomNav :showAdmin="userIsAdmin" />
  </div>
</template>

<style scoped>
.dashboard { display: flex; display: -webkit-box; display: -webkit-flex; min-height: 100vh; min-height: 100dvh; min-height: -webkit-fill-available; background: #000; color: #fff; -webkit-overflow-scrolling: touch; }
.sidebar { width: 260px; background: rgba(10, 10, 10, 0.95); border-right: 1px solid rgba(255, 255, 255, 0.1); display: flex; display: -webkit-box; display: -webkit-flex; -webkit-box-orient: vertical; -webkit-box-direction: normal; flex-direction: column; position: fixed; height: 100vh; height: 100dvh; height: -webkit-fill-available; z-index: 100; padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px); }
.nav-item.live-nav { background: linear-gradient(135deg, rgba(255, 68, 68, 0.1) 0%, rgba(255, 140, 0, 0.1) 100%); border: 1px solid rgba(255, 68, 68, 0.3); color: #ff6b6b; position: relative; }
.live-indicator { position: absolute; top: 50%; right: 12px; transform: translateY(-50%); width: 8px; height: 8px; background: #ff4444; border-radius: 50%; animation: live-pulse 1.5s infinite; }
@keyframes live-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
.mobile-nav-item.live-mobile { background: linear-gradient(135deg, rgba(255, 68, 68, 0.15) 0%, rgba(255, 140, 0, 0.15) 100%); border: 1px solid rgba(255, 68, 68, 0.3); color: #ff6b6b; }
.sidebar-header { padding: 25px; border-bottom: 1px solid rgba(255, 255, 255, 0.1); }
.sidebar-logo { height: 40px; width: auto; }
.sidebar-nav { flex: 1; padding: 20px 15px; display: flex; flex-direction: column; gap: 5px; overflow-y: auto; }
.nav-category { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 1px; color: rgba(255, 255, 255, 0.35); padding: 15px 15px 8px; font-weight: 600; }
.nav-category:first-child { padding-top: 0; }
.nav-item { display: flex; align-items: center; gap: 12px; padding: 12px 15px; border-radius: 10px; color: rgba(255, 255, 255, 0.6); text-decoration: none; transition: all 0.3s; font-weight: 500; }
.nav-item:hover { background: rgba(255, 255, 255, 0.05); color: #fff; }
.nav-item.active { background: rgba(255, 255, 255, 0.1); color: #fff; }
.nav-icon { width: 20px; height: 20px; }
.sidebar-footer { padding: 20px; border-top: 1px solid rgba(255, 255, 255, 0.1); }
.plan-badge-sidebar { background: rgba(255, 255, 255, 0.1); padding: 8px 15px; border-radius: 8px; text-align: center; font-weight: 600; margin-bottom: 15px; font-size: 0.9rem; }
.logout-btn { width: 100%; display: flex; align-items: center; justify-content: center; gap: 10px; padding: 12px; background: transparent; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; color: rgba(255, 255, 255, 0.6); cursor: pointer; transition: all 0.3s; }
.logout-btn:hover { border-color: #ef4444; color: #ef4444; }
.logout-icon { width: 18px; height: 18px; }

.mobile-menu-btn { display: none; position: fixed; top: 20px; right: 20px; width: 50px; height: 50px; border-radius: 12px; background: rgba(255, 255, 255, 0.95); border: none; box-shadow: 0 5px 30px rgba(0, 0, 0, 0.3); z-index: 1000; cursor: pointer; align-items: center; justify-content: center; }
.mobile-menu-btn svg { width: 28px; height: 28px; stroke: #000; }
.mobile-overlay { display: none; position: fixed; inset: 0; background: rgba(0, 0, 0, 0.7); z-index: 998; }
.mobile-menu { display: none; position: fixed; bottom: 0; left: 0; right: 0; background: #0a0a0a; border-top-left-radius: 25px; border-top-right-radius: 25px; padding: 25px; z-index: 999; transform: translateY(100%); transition: transform 0.3s ease; }
.mobile-menu.open { transform: translateY(0); }
.mobile-menu-header { text-align: center; margin-bottom: 20px; }
.mobile-logo { height: 35px; }
.mobile-nav { display: flex; flex-direction: column; gap: 8px; }
.mobile-nav-item { padding: 15px 20px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; color: #fff; font-weight: 500; cursor: pointer; transition: all 0.3s; text-align: left; }
.mobile-nav-item:hover, .mobile-nav-item.active { background: rgba(255, 255, 255, 0.1); border-color: rgba(255, 255, 255, 0.2); }
.mobile-logout { width: 100%; margin-top: 15px; padding: 15px; background: transparent; border: 1px solid #ef4444; border-radius: 12px; color: #ef4444; font-weight: 600; cursor: pointer; }

.main-content { flex: 1; margin-left: 260px; padding: 30px; }
.page-header { margin-bottom: 40px; }
.page-header h1 { font-size: 2rem; font-weight: 800; margin-bottom: 8px; }
.page-header p { color: rgba(255, 255, 255, 0.5); }

.settings-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 25px; max-width: 1200px; }
.settings-card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 15px; overflow: hidden; }
.card-header { display: flex; align-items: center; gap: 12px; padding: 20px 25px; border-bottom: 1px solid rgba(255, 255, 255, 0.1); }
.card-header svg { width: 22px; height: 22px; stroke: #fff; }
.card-header h3 { font-size: 1.1rem; font-weight: 600; }
.card-content { padding: 25px; }
.info-row { display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.05); }
.info-row:last-child { border-bottom: none; }
.label { color: rgba(255, 255, 255, 0.5); }
.value { font-weight: 500; }
.toggle-row { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.05); }
.toggle-row:last-child { border-bottom: none; }
.toggle { position: relative; width: 50px; height: 26px; }
.toggle input { opacity: 0; width: 0; height: 0; }
.slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background: rgba(255, 255, 255, 0.1); border-radius: 26px; transition: 0.3s; }
.slider:before { position: absolute; content: ""; height: 20px; width: 20px; left: 3px; bottom: 3px; background: #fff; border-radius: 50%; transition: 0.3s; }
.toggle input:checked + .slider { background: #22c55e; }
.toggle input:checked + .slider:before { transform: translateX(24px); }
.settings-btn { width: 100%; padding: 12px; background: rgba(255, 255, 255, 0.1); border: none; border-radius: 8px; color: #fff; font-weight: 600; cursor: pointer; transition: all 0.3s; }
.settings-btn:hover { background: rgba(255, 255, 255, 0.2); }

@media (max-width: 968px) {
  .sidebar { display: none; }
  .mobile-menu-btn { display: none; }
  .mobile-overlay { display: none; }
  .mobile-menu { display: none; }
  .main-content { margin-left: 0; padding: 20px; padding-bottom: 85px; }
  .settings-grid { grid-template-columns: 1fr; }
}

/* Avatar Section */
.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-bottom: 20px;
  margin-bottom: 15px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.avatar-wrapper {
  position: relative;
  cursor: pointer;
  margin-bottom: 12px;
}

.avatar-img {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid rgba(0, 217, 255, 0.5);
  box-shadow: 0 4px 20px rgba(0, 217, 255, 0.3);
}

.avatar-placeholder {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, #00d9ff, #0099cc);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  font-weight: bold;
  color: white;
  border: 3px solid rgba(0, 217, 255, 0.5);
}

.avatar-edit {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 28px;
  height: 28px;
  background: linear-gradient(135deg, #00d9ff, #0099cc);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  border: 2px solid #000;
}

.btn-change-photo {
  background: rgba(0, 217, 255, 0.1);
  border: 1px solid rgba(0, 217, 255, 0.3);
  color: #00d9ff;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-change-photo:hover {
  background: rgba(0, 217, 255, 0.2);
}

.plan-value {
  background: linear-gradient(135deg, #00d9ff, #0099cc);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
}

/* Modal de Avatar */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.avatar-modal {
  background: linear-gradient(145deg, rgba(13, 26, 43, 0.98), rgba(8, 18, 32, 0.98));
  border: 1px solid rgba(0, 217, 255, 0.2);
  border-radius: 16px;
  padding: 24px;
  max-width: 340px;
  width: 100%;
  text-align: center;
  position: relative;
}

.modal-close {
  position: absolute;
  top: 12px;
  right: 12px;
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.5);
  font-size: 24px;
  cursor: pointer;
}

.avatar-modal h3 {
  margin-bottom: 20px;
  font-size: 1.2rem;
}

.avatar-preview-container {
  margin: 20px auto;
}

.avatar-preview {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  object-fit: cover;
  border: 4px solid rgba(0, 217, 255, 0.4);
}

.avatar-preview-placeholder {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: linear-gradient(135deg, #00d9ff, #0099cc);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48px;
  font-weight: bold;
  color: white;
  margin: 0 auto;
}

.avatar-modal-actions {
  margin-top: 20px;
}

.btn-upload-avatar {
  background: linear-gradient(135deg, #00d9ff, #0099cc);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-upload-avatar:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 217, 255, 0.4);
}

.btn-upload-avatar:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.avatar-hint {
  margin-top: 12px;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
}

/* ===== PLAN BADGE ===== */
.plan-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 20px;
  font-weight: 700;
  font-size: 0.85rem;
}

.plan-badge.free {
  background: rgba(107, 114, 128, 0.2);
  color: #9ca3af;
}

.plan-badge.basic {
  background: rgba(205, 127, 50, 0.2);
  border: 1px solid rgba(205, 127, 50, 0.4);
  color: #cd7f32;
}

.plan-badge.pro {
  background: rgba(192, 192, 192, 0.2);
  border: 1px solid rgba(192, 192, 192, 0.4);
  color: #c0c0c0;
}

.plan-badge.ultra {
  background: rgba(255, 215, 0, 0.2);
  border: 1px solid rgba(255, 215, 0, 0.4);
  color: #ffd700;
}

.plan-badge.legend {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(236, 72, 153, 0.3));
  border: 1px solid rgba(139, 92, 246, 0.5);
  color: #a78bfa;
}

/* ===== PLAN CARD ===== */
.plan-card {
  background: rgba(255, 255, 255, 0.03);
  position: relative;
  overflow: hidden;
}

.plan-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #6b7280, #9ca3af);
}

.plan-card.basic::before {
  background: linear-gradient(90deg, #cd7f32, #daa520);
}

.plan-card.pro::before {
  background: linear-gradient(90deg, #c0c0c0, #e8e8e8);
}

.plan-card.ultra::before {
  background: linear-gradient(90deg, #ffd700, #ffed4a);
}

.plan-card.legend::before {
  background: linear-gradient(90deg, #8b5cf6, #ec4899);
}

.plan-card .card-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.plan-emoji {
  font-size: 1.5rem;
}

.plan-price {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 16px;
}

.plan-price .price-value {
  font-size: 1.8rem;
  font-weight: 800;
  color: #fff;
}

.plan-price .price-interval {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.5);
}

.plan-price.free .price-value {
  color: #9ca3af;
}

.plan-features {
  list-style: none;
  padding: 0;
  margin: 0 0 20px 0;
}

.plan-features li {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.85);
}

.plan-features li svg {
  width: 16px;
  height: 16px;
  stroke: #22c55e;
  flex-shrink: 0;
}

.btn-upgrade {
  display: block;
  width: 100%;
  background: linear-gradient(135deg, #8b5cf6, #6366f1);
  color: #fff;
  text-align: center;
  padding: 14px;
  border-radius: 10px;
  font-weight: 700;
  text-decoration: none;
  transition: all 0.3s;
}

.btn-upgrade:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(99, 102, 241, 0.4);
}

.btn-manage {
  display: block;
  width: 100%;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #fff;
  text-align: center;
  padding: 14px;
  border-radius: 10px;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.3s;
}

.btn-manage:hover {
  background: rgba(255, 255, 255, 0.15);
}

.legend-badge {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(236, 72, 153, 0.2));
  border: 1px solid rgba(139, 92, 246, 0.4);
  padding: 14px;
  border-radius: 10px;
  text-align: center;
  font-weight: 700;
  color: #a78bfa;
}
</style>
