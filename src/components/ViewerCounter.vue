<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { supabase } from '../lib/supabase'

const props = defineProps({
  isAdmin: { type: Boolean, default: false }
})

const viewerCount = ref(0)
const showTooltip = ref(false)
const channelRef = ref(null)

// Gerar ID único para esta sessão
const sessionId = `viewer_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

onMounted(async () => {
  if (!props.isAdmin) return

  try {
    // Usar Supabase Realtime Presence para contar viewers
    const channel = supabase.channel('palpites_viewers', {
      config: { presence: { key: sessionId } }
    })

    channel
      .on('presence', { event: 'sync' }, () => {
        const state = channel.presenceState()
        viewerCount.value = Object.keys(state).length
      })
      .on('presence', { event: 'join' }, ({ key, newPresences }) => {
        console.log('Novo viewer:', key)
      })
      .on('presence', { event: 'leave' }, ({ key, leftPresences }) => {
        console.log('Viewer saiu:', key)
      })

    await channel.subscribe(async (status) => {
      if (status === 'SUBSCRIBED') {
        await channel.track({ online_at: new Date().toISOString() })
      }
    })

    channelRef.value = channel

    // Fallback: buscar contagem do analytics
    await fetchAnalyticsCount()
  } catch (err) {
    console.error('Erro ao conectar presence:', err)
  }
})

onUnmounted(() => {
  if (channelRef.value) {
    supabase.removeChannel(channelRef.value)
  }
})

const fetchAnalyticsCount = async () => {
  try {
    // Buscar visitantes das últimas 5 minutos
    const fiveMinAgo = new Date(Date.now() - 5 * 60 * 1000).toISOString()
    const { count } = await supabase
      .from('page_views')
      .select('*', { count: 'exact', head: true })
      .gte('created_at', fiveMinAgo)
    
    if (count && count > viewerCount.value) {
      viewerCount.value = count
    }
  } catch (e) {
    // Tabela pode não existir ainda
  }
}
</script>

<template>
  <div 
    v-if="isAdmin" 
    class="viewer-counter"
    @mouseenter="showTooltip = true"
    @mouseleave="showTooltip = false"
  >
    <svg class="eye-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
      <circle cx="12" cy="12" r="3"/>
    </svg>
    <span class="viewer-count">{{ viewerCount }}</span>
    <span class="pulse-dot" :class="{ active: viewerCount > 0 }"></span>
    
    <Transition name="tooltip">
      <div v-if="showTooltip" class="viewer-tooltip">
        <strong>{{ viewerCount }}</strong> {{ viewerCount === 1 ? 'pessoa' : 'pessoas' }} visualizando palpites agora
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.viewer-counter {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 50px;
  padding: 8px 14px;
  cursor: default;
  position: relative;
  transition: all 0.3s ease;
}

.viewer-counter:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.25);
}

.eye-icon {
  width: 18px;
  height: 18px;
  color: #4caf50;
}

.viewer-count {
  font-size: 0.9rem;
  font-weight: 700;
  color: #fff;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  transition: all 0.3s ease;
}

.pulse-dot.active {
  background: #4caf50;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(1.3); }
}

.viewer-tooltip {
  position: absolute;
  top: calc(100% + 10px);
  left: 50%;
  transform: translateX(-50%);
  background: #1a1a1a;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.8);
  white-space: nowrap;
  z-index: 100;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.viewer-tooltip strong {
  color: #4caf50;
}

.viewer-tooltip::before {
  content: '';
  position: absolute;
  top: -6px;
  left: 50%;
  transform: translateX(-50%);
  border-left: 6px solid transparent;
  border-right: 6px solid transparent;
  border-bottom: 6px solid rgba(255, 255, 255, 0.15);
}

.tooltip-enter-active,
.tooltip-leave-active {
  transition: all 0.2s ease;
}

.tooltip-enter-from,
.tooltip-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-5px);
}
</style>
