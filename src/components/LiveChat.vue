<script setup>
/**
 * 💬 LiveChat.vue - Chat em tempo real
 * ODINENX v2.0
 */

import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { plans, getPlanBadge, canSendGif, canSendSticker } from '../lib/stripe'

const props = defineProps({
  messages: {
    type: Array,
    default: () => []
  },
  currentUser: {
    type: Object,
    default: null
  },
  userPlan: {
    type: String,
    default: 'free'
  }
})

const emit = defineEmits(['send'])
const input = defineModel('input', { type: String, default: '' })

const chatContainer = ref(null)
const showGifPicker = ref(false)
const showStickerPicker = ref(false)
const showEmojiPicker = ref(false)

// Emojis básicos disponíveis para todos
const basicEmojis = ['😀', '😂', '🔥', '⚽', '🎉', '👏', '💪', '😱', '😭', '🙏', '❤️', '💯', '🚀', '⭐', '👑']

// GIFs populares (simulado - em produção usar Giphy API)
const popularGifs = [
  { id: 'goal', url: 'https://media.giphy.com/media/l0MYGb1LuZ3n7dRnO/giphy.gif', name: 'Gol!' },
  { id: 'celebrate', url: 'https://media.giphy.com/media/26u4cqiYI30juCOGY/giphy.gif', name: 'Comemorando' },
  { id: 'sad', url: 'https://media.giphy.com/media/d2lcHJTG5Tscg/giphy.gif', name: 'Triste' },
  { id: 'angry', url: 'https://media.giphy.com/media/l1J9u3TZfpmeDLkD6/giphy.gif', name: 'Bravo' },
  { id: 'wow', url: 'https://media.giphy.com/media/5VKbvrjxpVJCM/giphy.gif', name: 'Uau!' },
  { id: 'clap', url: 'https://media.giphy.com/media/26gsjCZpPolPr3sBy/giphy.gif', name: 'Aplausos' }
]

// Stickers exclusivos (Pro+)
const exclusiveStickers = [
  { id: 'fire_ball', name: '🔥⚽', premium: true },
  { id: 'trophy', name: '🏆', premium: true },
  { id: 'money', name: '💰', premium: true },
  { id: 'king', name: '👑', premium: true }
]

// Auto-scroll quando novas mensagens chegam
watch(() => props.messages.length, async () => {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
})

onMounted(() => {
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
})

// Computed
const canUseGifs = computed(() => canSendGif(props.userPlan))
const canUseStickers = computed(() => canSendSticker(props.userPlan))

// Formatar mensagem
function formatMessage(msg) {
  const badge = getPlanBadge(msg.user_plan)
  return {
    ...msg,
    badge,
    isOwn: msg.user_id === props.currentUser?.id,
    isSystem: msg.message_type === 'system',
    formattedTime: new Date(msg.created_at).toLocaleTimeString('pt-BR', { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  }
}

// Enviar mensagem
function handleSend() {
  if (!input.value.trim()) return
  emit('send')
}

// Adicionar emoji
function addEmoji(emoji) {
  input.value += emoji
  showEmojiPicker.value = false
}

// Enviar GIF
function sendGif(gif) {
  if (!canUseGifs.value) return
  input.value = `[GIF:${gif.url}]`
  emit('send')
  showGifPicker.value = false
}

// Enviar Sticker
function sendSticker(sticker) {
  if (!canUseStickers.value) return
  input.value = `[STICKER:${sticker.id}]`
  emit('send')
  showStickerPicker.value = false
}

// Renderizar conteúdo da mensagem
function renderContent(msg) {
  if (msg.message_type === 'gif' || msg.message.startsWith('[GIF:')) {
    const url = msg.gif_url || msg.message.match(/\[GIF:(.*?)\]/)?.[1]
    return { type: 'gif', url }
  }
  if (msg.message_type === 'sticker' || msg.message.startsWith('[STICKER:')) {
    return { type: 'sticker', id: msg.sticker_id || msg.message.match(/\[STICKER:(.*?)\]/)?.[1] }
  }
  return { type: 'text', content: msg.message }
}
</script>

<template>
  <div class="live-chat">
    <!-- Mensagens -->
    <div class="messages-container" ref="chatContainer">
      <TransitionGroup name="message">
        <div 
          v-for="msg in messages" 
          :key="msg.id"
          class="message"
          :class="{ 
            own: formatMessage(msg).isOwn,
            system: formatMessage(msg).isSystem,
            highlighted: msg.is_highlighted,
            [msg.user_plan]: true
          }"
        >
          <!-- Mensagem de Sistema -->
          <template v-if="formatMessage(msg).isSystem">
            <div class="system-message">
              {{ msg.message }}
            </div>
          </template>
          
          <!-- Mensagem Normal -->
          <template v-else>
            <div class="message-header">
              <span class="badge" v-if="formatMessage(msg).badge">
                {{ formatMessage(msg).badge }}
              </span>
              <span class="username" :class="msg.user_plan">
                {{ msg.username }}
              </span>
              <span class="time">{{ formatMessage(msg).formattedTime }}</span>
            </div>
            
            <div class="message-content">
              <!-- GIF -->
              <template v-if="renderContent(msg).type === 'gif'">
                <img :src="renderContent(msg).url" class="gif-content" alt="GIF" />
              </template>
              
              <!-- Sticker -->
              <template v-else-if="renderContent(msg).type === 'sticker'">
                <span class="sticker-content">{{ renderContent(msg).id }}</span>
              </template>
              
              <!-- Texto -->
              <template v-else>
                {{ msg.message }}
              </template>
            </div>
          </template>
        </div>
      </TransitionGroup>
    </div>
    
    <!-- Input Area -->
    <div class="input-area">
      <!-- Pickers -->
      <div class="pickers">
        <!-- Emoji Picker -->
        <div class="picker-container">
          <button 
            class="picker-btn" 
            @click="showEmojiPicker = !showEmojiPicker"
            title="Emojis"
          >
            😀
          </button>
          <div class="picker-dropdown" v-if="showEmojiPicker">
            <button 
              v-for="emoji in basicEmojis" 
              :key="emoji"
              class="emoji-btn"
              @click="addEmoji(emoji)"
            >
              {{ emoji }}
            </button>
          </div>
        </div>
        
        <!-- GIF Picker -->
        <div class="picker-container">
          <button 
            class="picker-btn"
            :class="{ disabled: !canUseGifs }"
            @click="canUseGifs && (showGifPicker = !showGifPicker)"
            :title="canUseGifs ? 'GIFs' : 'GIFs disponíveis a partir do Basic'"
          >
            GIF
          </button>
          <div class="picker-dropdown gif-picker" v-if="showGifPicker && canUseGifs">
            <div 
              v-for="gif in popularGifs" 
              :key="gif.id"
              class="gif-option"
              @click="sendGif(gif)"
            >
              <img :src="gif.url" :alt="gif.name" />
            </div>
          </div>
        </div>
        
        <!-- Sticker Picker -->
        <div class="picker-container">
          <button 
            class="picker-btn"
            :class="{ disabled: !canUseStickers }"
            @click="canUseStickers && (showStickerPicker = !showStickerPicker)"
            :title="canUseStickers ? 'Stickers' : 'Stickers disponíveis a partir do Pro'"
          >
            ⭐
          </button>
          <div class="picker-dropdown" v-if="showStickerPicker && canUseStickers">
            <button 
              v-for="sticker in exclusiveStickers" 
              :key="sticker.id"
              class="sticker-btn"
              @click="sendSticker(sticker)"
            >
              {{ sticker.name }}
            </button>
          </div>
        </div>
      </div>
      
      <!-- Input -->
      <input 
        type="text"
        v-model="input"
        @keyup.enter="handleSend"
        placeholder="Digite sua mensagem..."
        class="chat-input"
      />
      
      <!-- Send Button -->
      <button class="send-btn" @click="handleSend">
        ➤
      </button>
    </div>
  </div>
</template>

<style scoped>
.live-chat {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: rgba(0,0,0,0.2);
}

/* Messages Container */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

/* Message */
.message {
  max-width: 80%;
  padding: 0.5rem 0.75rem;
  border-radius: 12px;
  background: rgba(255,255,255,0.05);
  animation: slideIn 0.2s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message.own {
  align-self: flex-end;
  background: rgba(255,215,0,0.2);
}

.message.system {
  align-self: center;
  max-width: 100%;
  background: transparent;
}

.system-message {
  color: #888;
  font-size: 0.85rem;
  font-style: italic;
  text-align: center;
}

.message.highlighted {
  background: linear-gradient(135deg, rgba(255,215,0,0.3), rgba(255,140,0,0.3));
  border: 1px solid rgba(255,215,0,0.5);
}

/* Username colors by plan */
.message.elite .username {
  color: #ffd700;
  text-shadow: 0 0 10px rgba(255,215,0,0.5);
}

.message.pro .username {
  color: #c0c0c0;
}

.message.basic .username {
  color: #cd7f32;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}

.badge {
  font-size: 0.9rem;
}

.username {
  font-weight: 600;
  font-size: 0.85rem;
}

.time {
  font-size: 0.7rem;
  color: #666;
  margin-left: auto;
}

.message-content {
  font-size: 0.95rem;
  word-break: break-word;
}

.gif-content {
  max-width: 200px;
  max-height: 150px;
  border-radius: 8px;
}

.sticker-content {
  font-size: 3rem;
}

/* Input Area */
.input-area {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background: rgba(0,0,0,0.3);
  border-top: 1px solid rgba(255,255,255,0.1);
}

.pickers {
  display: flex;
  gap: 0.25rem;
}

.picker-container {
  position: relative;
}

.picker-btn {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 8px;
  background: rgba(255,255,255,0.1);
  color: white;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
}

.picker-btn:hover:not(.disabled) {
  background: rgba(255,255,255,0.2);
}

.picker-btn.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.picker-dropdown {
  position: absolute;
  bottom: 100%;
  left: 0;
  background: #1e1e3f;
  border-radius: 12px;
  padding: 0.5rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  max-width: 250px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.5);
  border: 1px solid rgba(255,255,255,0.1);
  z-index: 100;
}

.emoji-btn,
.sticker-btn {
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  font-size: 1.2rem;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.2s;
}

.emoji-btn:hover,
.sticker-btn:hover {
  background: rgba(255,255,255,0.1);
  transform: scale(1.1);
}

.gif-picker {
  width: 300px;
  max-height: 200px;
  overflow-y: auto;
}

.gif-option {
  cursor: pointer;
  border-radius: 8px;
  overflow: hidden;
}

.gif-option img {
  width: 90px;
  height: 70px;
  object-fit: cover;
}

.gif-option:hover {
  opacity: 0.8;
}

/* Chat Input */
.chat-input {
  flex: 1;
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 20px;
  background: rgba(255,255,255,0.1);
  color: white;
  font-size: 0.95rem;
  outline: none;
}

.chat-input::placeholder {
  color: #666;
}

.chat-input:focus {
  background: rgba(255,255,255,0.15);
}

/* Send Button */
.send-btn {
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 50%;
  background: linear-gradient(135deg, #ffd700 0%, #ff8c00 100%);
  color: #000;
  font-size: 1.1rem;
  cursor: pointer;
  transition: all 0.2s;
}

.send-btn:hover {
  transform: scale(1.1);
}

/* Transitions */
.message-enter-active {
  transition: all 0.3s ease;
}

.message-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

/* Scrollbar */
.messages-container::-webkit-scrollbar {
  width: 6px;
}

.messages-container::-webkit-scrollbar-track {
  background: transparent;
}

.messages-container::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.2);
  border-radius: 3px;
}
</style>
