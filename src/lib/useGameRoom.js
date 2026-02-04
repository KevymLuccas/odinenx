/**
 * 🏟️ useGameRoom - Composable para gerenciar salas de jogo ao vivo
 * ODINENX v2.0
 */

import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { supabase } from './supabase'
import { plans, getPlanBadge, getPlanOrder, canSendGif, canSendSticker, getCelebrationEffect } from './stripe'

// Estado global das salas
const currentRoom = ref(null)
const roomUsers = ref([])
const roomMessages = ref([])
const userOdds = ref([])
const reactions = ref([])
const isConnected = ref(false)
const isLoading = ref(false)
const error = ref(null)

// Channels do Supabase Realtime
let roomChannel = null
let messagesChannel = null
let usersChannel = null
let oddsChannel = null
let reactionsChannel = null

/**
 * Hook principal para salas de jogo
 */
export function useGameRoom() {
  
  // ============================================
  // COMPUTED
  // ============================================
  
  const viewersCount = computed(() => {
    return roomUsers.value.filter(u => u.is_online).length
  })
  
  const sortedUsers = computed(() => {
    return [...roomUsers.value]
      .filter(u => u.is_online)
      .sort((a, b) => getPlanOrder(a.plan) - getPlanOrder(b.plan))
  })
  
  const matchScore = computed(() => {
    if (!currentRoom.value) return '0 x 0'
    return `${currentRoom.value.home_score} x ${currentRoom.value.away_score}`
  })
  
  const isLive = computed(() => {
    return currentRoom.value?.status === 'live'
  })
  
  // ============================================
  // MÉTODOS - SALA
  // ============================================
  
  /**
   * Buscar salas ao vivo
   */
  async function fetchLiveRooms() {
    isLoading.value = true
    try {
      const { data, error: err } = await supabase
        .from('game_rooms')
        .select('*, room_users(count)')
        .in('status', ['live', 'scheduled'])
        .order('start_time', { ascending: true })
      
      if (err) throw err
      return data || []
    } catch (err) {
      error.value = err.message
      return []
    } finally {
      isLoading.value = false
    }
  }
  
  /**
   * Entrar em uma sala
   */
  async function joinRoom(roomId, userId, userProfile, selectedOdds = []) {
    isLoading.value = true
    error.value = null
    
    try {
      // 1. Buscar dados da sala
      const { data: room, error: roomErr } = await supabase
        .from('game_rooms')
        .select('*')
        .eq('id', roomId)
        .single()
      
      if (roomErr) throw roomErr
      currentRoom.value = room
      
      // 2. Registrar usuário na sala
      const { error: joinErr } = await supabase
        .from('room_users')
        .upsert({
          room_id: roomId,
          user_id: userId,
          username: userProfile.username || userProfile.email?.split('@')[0] || 'Anônimo',
          plan: userProfile.plan || 'free',
          avatar_url: userProfile.avatar_url,
          selected_odds: selectedOdds,
          is_online: true
        }, {
          onConflict: 'room_id,user_id'
        })
      
      if (joinErr) throw joinErr
      
      // 3. Salvar odds selecionadas
      if (selectedOdds.length > 0) {
        const oddsToInsert = selectedOdds.map(odd => ({
          room_id: roomId,
          user_id: userId,
          odd_type: odd.type,
          odd_pick: odd.pick,
          odd_value: odd.value,
          status: 'pending'
        }))
        
        await supabase.from('user_odds').insert(oddsToInsert)
      }
      
      // 4. Carregar dados iniciais
      await Promise.all([
        loadRoomUsers(roomId),
        loadRoomMessages(roomId),
        loadUserOdds(roomId)
      ])
      
      // 5. Configurar Realtime
      setupRealtimeSubscriptions(roomId)
      
      // 6. Enviar mensagem de entrada
      await sendSystemMessage(roomId, `${userProfile.username || 'Usuário'} entrou na sala`)
      
      isConnected.value = true
      return true
      
    } catch (err) {
      error.value = err.message
      console.error('Erro ao entrar na sala:', err)
      return false
    } finally {
      isLoading.value = false
    }
  }
  
  /**
   * Sair da sala
   */
  async function leaveRoom(roomId, userId) {
    try {
      // Marcar como offline
      await supabase
        .from('room_users')
        .update({ is_online: false })
        .eq('room_id', roomId)
        .eq('user_id', userId)
      
      // Remover subscriptions
      cleanupSubscriptions()
      
      currentRoom.value = null
      roomUsers.value = []
      roomMessages.value = []
      userOdds.value = []
      isConnected.value = false
      
    } catch (err) {
      console.error('Erro ao sair da sala:', err)
    }
  }
  
  // ============================================
  // MÉTODOS - MENSAGENS
  // ============================================
  
  /**
   * Enviar mensagem no chat
   */
  async function sendMessage(roomId, userId, userProfile, message, type = 'text', extras = {}) {
    // Validar permissões
    const plan = userProfile.plan || 'free'
    
    if (type === 'gif' && !canSendGif(plan)) {
      error.value = 'GIFs disponíveis a partir do plano Basic'
      return false
    }
    
    if (type === 'sticker' && !canSendSticker(plan)) {
      error.value = 'Stickers disponíveis a partir do plano Pro'
      return false
    }
    
    try {
      const { error: err } = await supabase
        .from('room_messages')
        .insert({
          room_id: roomId,
          user_id: userId,
          username: userProfile.username || 'Anônimo',
          user_plan: plan,
          message: message,
          message_type: type,
          gif_url: extras.gifUrl || null,
          sticker_id: extras.stickerId || null
        })
      
      if (err) throw err
      return true
      
    } catch (err) {
      error.value = err.message
      return false
    }
  }
  
  /**
   * Enviar mensagem de sistema
   */
  async function sendSystemMessage(roomId, message) {
    try {
      await supabase
        .from('room_messages')
        .insert({
          room_id: roomId,
          user_id: null,
          username: 'Sistema',
          user_plan: 'system',
          message: message,
          message_type: 'system'
        })
    } catch (err) {
      console.error('Erro ao enviar mensagem de sistema:', err)
    }
  }
  
  /**
   * Enviar reação rápida
   */
  async function sendReaction(roomId, userId, reaction) {
    try {
      await supabase
        .from('room_reactions')
        .insert({
          room_id: roomId,
          user_id: userId,
          reaction: reaction
        })
      return true
    } catch (err) {
      return false
    }
  }
  
  // ============================================
  // MÉTODOS - DADOS
  // ============================================
  
  async function loadRoomUsers(roomId) {
    const { data } = await supabase
      .from('room_users')
      .select('*')
      .eq('room_id', roomId)
      .eq('is_online', true)
    
    roomUsers.value = data || []
  }
  
  async function loadRoomMessages(roomId, limit = 100) {
    const { data } = await supabase
      .from('room_messages')
      .select('*')
      .eq('room_id', roomId)
      .order('created_at', { ascending: true })
      .limit(limit)
    
    roomMessages.value = data || []
  }
  
  async function loadUserOdds(roomId) {
    const { data } = await supabase
      .from('user_odds')
      .select('*')
      .eq('room_id', roomId)
    
    userOdds.value = data || []
  }
  
  // ============================================
  // REALTIME SUBSCRIPTIONS
  // ============================================
  
  function setupRealtimeSubscriptions(roomId) {
    // Canal principal da sala (placar)
    roomChannel = supabase
      .channel(`room:${roomId}`)
      .on('postgres_changes', {
        event: 'UPDATE',
        schema: 'public',
        table: 'game_rooms',
        filter: `id=eq.${roomId}`
      }, (payload) => {
        const oldScore = `${currentRoom.value?.home_score}-${currentRoom.value?.away_score}`
        currentRoom.value = { ...currentRoom.value, ...payload.new }
        const newScore = `${payload.new.home_score}-${payload.new.away_score}`
        
        // Detectar gol
        if (oldScore !== newScore) {
          triggerGoalCelebration(payload.new)
        }
      })
      .subscribe()
    
    // Canal de mensagens
    messagesChannel = supabase
      .channel(`messages:${roomId}`)
      .on('postgres_changes', {
        event: 'INSERT',
        schema: 'public',
        table: 'room_messages',
        filter: `room_id=eq.${roomId}`
      }, (payload) => {
        roomMessages.value.push(payload.new)
        // Manter apenas últimas 200 mensagens
        if (roomMessages.value.length > 200) {
          roomMessages.value = roomMessages.value.slice(-200)
        }
      })
      .subscribe()
    
    // Canal de usuários
    usersChannel = supabase
      .channel(`users:${roomId}`)
      .on('postgres_changes', {
        event: '*',
        schema: 'public',
        table: 'room_users',
        filter: `room_id=eq.${roomId}`
      }, async () => {
        await loadRoomUsers(roomId)
      })
      .subscribe()
    
    // Canal de odds
    oddsChannel = supabase
      .channel(`odds:${roomId}`)
      .on('postgres_changes', {
        event: '*',
        schema: 'public',
        table: 'user_odds',
        filter: `room_id=eq.${roomId}`
      }, (payload) => {
        if (payload.eventType === 'UPDATE') {
          const idx = userOdds.value.findIndex(o => o.id === payload.new.id)
          if (idx >= 0) {
            userOdds.value[idx] = payload.new
            // Trigger celebração se ganhou
            if (payload.new.status === 'won' && payload.old?.status === 'pending') {
              triggerOddWonCelebration(payload.new)
            }
          }
        } else if (payload.eventType === 'INSERT') {
          userOdds.value.push(payload.new)
        }
      })
      .subscribe()
    
    // Canal de reações
    reactionsChannel = supabase
      .channel(`reactions:${roomId}`)
      .on('postgres_changes', {
        event: 'INSERT',
        schema: 'public',
        table: 'room_reactions',
        filter: `room_id=eq.${roomId}`
      }, (payload) => {
        reactions.value.push(payload.new)
        // Remover após 3 segundos (animação)
        setTimeout(() => {
          reactions.value = reactions.value.filter(r => r.id !== payload.new.id)
        }, 3000)
      })
      .subscribe()
  }
  
  function cleanupSubscriptions() {
    if (roomChannel) supabase.removeChannel(roomChannel)
    if (messagesChannel) supabase.removeChannel(messagesChannel)
    if (usersChannel) supabase.removeChannel(usersChannel)
    if (oddsChannel) supabase.removeChannel(oddsChannel)
    if (reactionsChannel) supabase.removeChannel(reactionsChannel)
  }
  
  // ============================================
  // CELEBRAÇÕES
  // ============================================
  
  const celebrationEvent = ref(null)
  
  function triggerGoalCelebration(roomData) {
    celebrationEvent.value = {
      type: 'goal',
      data: roomData,
      timestamp: Date.now()
    }
    
    // Auto-limpar após animação
    setTimeout(() => {
      celebrationEvent.value = null
    }, 5000)
  }
  
  function triggerOddWonCelebration(oddData) {
    celebrationEvent.value = {
      type: 'odd_won',
      data: oddData,
      timestamp: Date.now()
    }
    
    setTimeout(() => {
      celebrationEvent.value = null
    }, 5000)
  }
  
  // ============================================
  // SALAS PRIVADAS
  // ============================================
  
  async function createPrivateRoom(userId, userPlan, fixtureData) {
    const maxRooms = plans[userPlan]?.limits?.salasPrivadas || 0
    
    if (maxRooms === 0) {
      error.value = 'Salas privadas disponíveis a partir do plano Basic'
      return null
    }
    
    // Verificar quantas salas o usuário já tem
    if (maxRooms > 0) {
      const { count } = await supabase
        .from('game_rooms')
        .select('*', { count: 'exact', head: true })
        .eq('owner_id', userId)
        .eq('is_private', true)
      
      if (count >= maxRooms) {
        error.value = `Você já atingiu o limite de ${maxRooms} sala(s) privada(s)`
        return null
      }
    }
    
    // Gerar código único
    const privateCode = Math.random().toString(36).substring(2, 8).toUpperCase()
    
    const { data, error: err } = await supabase
      .from('game_rooms')
      .insert({
        fixture_id: fixtureData.fixture_id,
        home_team: fixtureData.home_team,
        away_team: fixtureData.away_team,
        home_team_logo: fixtureData.home_logo,
        away_team_logo: fixtureData.away_logo,
        league: fixtureData.league,
        is_private: true,
        private_code: privateCode,
        owner_id: userId,
        status: 'scheduled'
      })
      .select()
      .single()
    
    if (err) {
      error.value = err.message
      return null
    }
    
    return data
  }
  
  async function joinPrivateRoom(privateCode, userId, userProfile) {
    const { data: room, error: err } = await supabase
      .from('game_rooms')
      .select('*')
      .eq('private_code', privateCode.toUpperCase())
      .single()
    
    if (err || !room) {
      error.value = 'Sala não encontrada'
      return null
    }
    
    return joinRoom(room.id, userId, userProfile)
  }
  
  // ============================================
  // LIFECYCLE
  // ============================================
  
  onUnmounted(() => {
    cleanupSubscriptions()
  })
  
  // ============================================
  // RETURN
  // ============================================
  
  return {
    // State
    currentRoom,
    roomUsers,
    roomMessages,
    userOdds,
    reactions,
    isConnected,
    isLoading,
    error,
    celebrationEvent,
    
    // Computed
    viewersCount,
    sortedUsers,
    matchScore,
    isLive,
    
    // Methods
    fetchLiveRooms,
    joinRoom,
    leaveRoom,
    sendMessage,
    sendReaction,
    createPrivateRoom,
    joinPrivateRoom,
    
    // Helpers
    getPlanBadge,
    canSendGif,
    canSendSticker,
    getCelebrationEffect
  }
}

export default useGameRoom
