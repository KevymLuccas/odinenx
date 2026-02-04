<script setup>
/**
 * 🎨 CustomizationStore.vue - Loja de Customização Elite
 * ODINENX v2.0
 */

import { ref, computed, onMounted } from 'vue'
import { supabase } from '../lib/supabase'
import { getSubscriptionStatus } from '../lib/stripe'

const props = defineProps({
  userId: { type: String, required: true }
})

const emit = defineEmits(['close', 'purchase'])

// State
const loading = ref(true)
const purchasing = ref(false)
const userPlan = ref('free')
const userCoins = ref(0)
const ownedItems = ref([])
const equippedItems = ref({})
const activeCategory = ref('effects')
const notification = ref('')

// Categorias da loja
const categories = [
  { id: 'effects', name: '✨ Efeitos', description: 'Efeitos visuais exclusivos' },
  { id: 'colors', name: '🎨 Cores', description: 'Cores personalizadas para seu nome' },
  { id: 'frames', name: '🖼️ Molduras', description: 'Molduras para seu avatar' },
  { id: 'celebrations', name: '🎉 Celebrações', description: 'Animações de celebração' },
  { id: 'sounds', name: '🔊 Sons', description: 'Sons personalizados' }
]

// Itens da loja (em produção, viriam do banco)
const storeItems = {
  effects: [
    {
      id: 'effect_fire',
      name: 'Aura de Fogo',
      description: 'Seu nome fica em chamas',
      price: 500,
      preview: '🔥',
      rarity: 'epic'
    },
    {
      id: 'effect_ice',
      name: 'Aura de Gelo',
      description: 'Cristais de gelo ao redor do nome',
      price: 500,
      preview: '❄️',
      rarity: 'epic'
    },
    {
      id: 'effect_rainbow',
      name: 'Arco-íris',
      description: 'Nome com cores do arco-íris',
      price: 800,
      preview: '🌈',
      rarity: 'legendary'
    },
    {
      id: 'effect_sparkle',
      name: 'Brilhantes',
      description: 'Partículas brilhantes',
      price: 300,
      preview: '✨',
      rarity: 'rare'
    },
    {
      id: 'effect_lightning',
      name: 'Raios',
      description: 'Efeito elétrico',
      price: 600,
      preview: '⚡',
      rarity: 'epic'
    }
  ],
  colors: [
    {
      id: 'color_gold',
      name: 'Dourado Premium',
      description: 'Nome em dourado brilhante',
      price: 200,
      preview: '#ffd700',
      rarity: 'rare'
    },
    {
      id: 'color_neon_pink',
      name: 'Rosa Neon',
      description: 'Rosa vibrante',
      price: 150,
      preview: '#ff1493',
      rarity: 'common'
    },
    {
      id: 'color_cyber_blue',
      name: 'Azul Cyber',
      description: 'Azul futurista',
      price: 150,
      preview: '#00bfff',
      rarity: 'common'
    },
    {
      id: 'color_toxic_green',
      name: 'Verde Tóxico',
      description: 'Verde radioativo',
      price: 200,
      preview: '#39ff14',
      rarity: 'rare'
    },
    {
      id: 'color_gradient_sunset',
      name: 'Gradiente Sunset',
      description: 'Gradiente de cores do pôr do sol',
      price: 400,
      preview: 'linear-gradient(90deg, #ff6b6b, #ffd93d)',
      rarity: 'epic'
    }
  ],
  frames: [
    {
      id: 'frame_diamond',
      name: 'Diamante',
      description: 'Moldura de diamante',
      price: 600,
      preview: '💎',
      rarity: 'legendary'
    },
    {
      id: 'frame_crown',
      name: 'Coroa Real',
      description: 'Moldura com coroa',
      price: 400,
      preview: '👑',
      rarity: 'epic'
    },
    {
      id: 'frame_star',
      name: 'Estrelas',
      description: 'Moldura com estrelas',
      price: 250,
      preview: '⭐',
      rarity: 'rare'
    },
    {
      id: 'frame_fire',
      name: 'Chamas',
      description: 'Moldura de fogo',
      price: 350,
      preview: '🔥',
      rarity: 'epic'
    }
  ],
  celebrations: [
    {
      id: 'celeb_fireworks',
      name: 'Fogos de Artifício',
      description: 'Explosão de fogos',
      price: 300,
      preview: '🎆',
      rarity: 'rare'
    },
    {
      id: 'celeb_confetti_gold',
      name: 'Confete Dourado',
      description: 'Chuva de confete dourado',
      price: 250,
      preview: '🎊',
      rarity: 'rare'
    },
    {
      id: 'celeb_party',
      name: 'Festa Completa',
      description: 'Balões + confete + música',
      price: 500,
      preview: '🎉',
      rarity: 'epic'
    },
    {
      id: 'celeb_lightning',
      name: 'Tempestade',
      description: 'Raios dramáticos',
      price: 400,
      preview: '🌩️',
      rarity: 'epic'
    }
  ],
  sounds: [
    {
      id: 'sound_goal',
      name: 'Narração Gol',
      description: 'GOOOOOOL clássico',
      price: 150,
      preview: '📢',
      rarity: 'common'
    },
    {
      id: 'sound_win',
      name: 'Vitória Épica',
      description: 'Fanfarra de vitória',
      price: 200,
      preview: '🎺',
      rarity: 'rare'
    },
    {
      id: 'sound_money',
      name: 'Ca-ching!',
      description: 'Som de dinheiro',
      price: 250,
      preview: '💰',
      rarity: 'rare'
    },
    {
      id: 'sound_meme',
      name: 'Meme Pack',
      description: 'Sons de memes populares',
      price: 400,
      preview: '🤣',
      rarity: 'epic'
    }
  ]
}

// Current items
const currentItems = computed(() => storeItems[activeCategory.value] || [])

// Check if item is owned
const isOwned = (itemId) => ownedItems.value.includes(itemId)

// Check if item is equipped
const isEquipped = (itemId) => {
  return Object.values(equippedItems.value).includes(itemId)
}

// Rarity colors
const rarityColors = {
  common: '#aaa',
  rare: '#3498db',
  epic: '#9b59b6',
  legendary: '#f39c12'
}

// Load user data
onMounted(async () => {
  try {
    // Get subscription
    const sub = await getSubscriptionStatus(props.userId)
    userPlan.value = sub.plan || 'free'
    
    // Get user customizations
    const { data: customs } = await supabase
      .from('user_customizations')
      .select('*')
      .eq('user_id', props.userId)
      .single()
    
    if (customs) {
      userCoins.value = customs.coins || 0
      ownedItems.value = customs.owned_items || []
      equippedItems.value = customs.equipped_items || {}
    }
  } catch (err) {
    console.error('Erro ao carregar dados:', err)
  } finally {
    loading.value = false
  }
})

// Purchase item
async function purchaseItem(item) {
  if (isOwned(item.id)) return
  if (userCoins.value < item.price) {
    showNotification('Moedas insuficientes! 💰')
    return
  }
  
  purchasing.value = true
  
  try {
    const newCoins = userCoins.value - item.price
    const newOwned = [...ownedItems.value, item.id]
    
    const { error } = await supabase
      .from('user_customizations')
      .upsert({
        user_id: props.userId,
        coins: newCoins,
        owned_items: newOwned,
        updated_at: new Date().toISOString()
      })
    
    if (error) throw error
    
    userCoins.value = newCoins
    ownedItems.value = newOwned
    
    showNotification(`${item.name} adquirido! ✨`)
    emit('purchase', item)
  } catch (err) {
    console.error('Erro na compra:', err)
    showNotification('Erro ao comprar item')
  } finally {
    purchasing.value = false
  }
}

// Equip item
async function equipItem(item) {
  if (!isOwned(item.id)) return
  
  try {
    const newEquipped = { ...equippedItems.value }
    newEquipped[activeCategory.value] = item.id
    
    const { error } = await supabase
      .from('user_customizations')
      .upsert({
        user_id: props.userId,
        equipped_items: newEquipped,
        updated_at: new Date().toISOString()
      })
    
    if (error) throw error
    
    equippedItems.value = newEquipped
    showNotification(`${item.name} equipado!`)
  } catch (err) {
    console.error('Erro ao equipar:', err)
    showNotification('Erro ao equipar item')
  }
}

// Unequip item
async function unequipItem() {
  try {
    const newEquipped = { ...equippedItems.value }
    delete newEquipped[activeCategory.value]
    
    const { error } = await supabase
      .from('user_customizations')
      .upsert({
        user_id: props.userId,
        equipped_items: newEquipped,
        updated_at: new Date().toISOString()
      })
    
    if (error) throw error
    
    equippedItems.value = newEquipped
    showNotification('Item removido')
  } catch (err) {
    console.error('Erro ao remover:', err)
  }
}

// Show notification
function showNotification(message) {
  notification.value = message
  setTimeout(() => notification.value = '', 3000)
}
</script>

<template>
  <div class="store-overlay" @click.self="$emit('close')">
    <div class="store-modal">
      <!-- Header -->
      <div class="store-header">
        <div class="header-left">
          <h2>🎨 Loja de Customização</h2>
          <span class="elite-badge">👑 Elite Exclusivo</span>
        </div>
        <div class="header-right">
          <div class="coins-display">
            <span class="coin-icon">🪙</span>
            <span class="coin-amount">{{ userCoins.toLocaleString() }}</span>
          </div>
          <button class="close-btn" @click="$emit('close')">✕</button>
        </div>
      </div>
      
      <!-- Not Elite Warning -->
      <div v-if="userPlan !== 'elite'" class="not-elite-warning">
        <p>⚠️ A loja de customização é exclusiva para usuários Elite</p>
        <router-link to="/pricing" class="upgrade-link">
          Fazer Upgrade 👑
        </router-link>
      </div>
      
      <!-- Store Content -->
      <div v-else class="store-content">
        <!-- Categories -->
        <div class="categories">
          <button
            v-for="cat in categories"
            :key="cat.id"
            class="category-btn"
            :class="{ active: activeCategory === cat.id }"
            @click="activeCategory = cat.id"
          >
            {{ cat.name }}
          </button>
        </div>
        
        <!-- Items Grid -->
        <div class="items-grid">
          <div
            v-for="item in currentItems"
            :key="item.id"
            class="item-card"
            :class="{ 
              owned: isOwned(item.id),
              equipped: isEquipped(item.id)
            }"
          >
            <!-- Rarity indicator -->
            <div 
              class="rarity-bar" 
              :style="{ background: rarityColors[item.rarity] }"
            ></div>
            
            <!-- Preview -->
            <div class="item-preview">
              <span v-if="item.preview.length < 5">{{ item.preview }}</span>
              <div 
                v-else 
                class="color-preview"
                :style="{ background: item.preview }"
              ></div>
            </div>
            
            <!-- Info -->
            <div class="item-info">
              <h4>{{ item.name }}</h4>
              <p>{{ item.description }}</p>
              <div class="rarity-tag" :style="{ color: rarityColors[item.rarity] }">
                {{ item.rarity.toUpperCase() }}
              </div>
            </div>
            
            <!-- Actions -->
            <div class="item-actions">
              <template v-if="isOwned(item.id)">
                <button 
                  v-if="isEquipped(item.id)"
                  class="btn-unequip"
                  @click="unequipItem"
                >
                  ✓ Equipado
                </button>
                <button 
                  v-else
                  class="btn-equip"
                  @click="equipItem(item)"
                >
                  Equipar
                </button>
              </template>
              <template v-else>
                <button 
                  class="btn-buy"
                  :disabled="userCoins < item.price || purchasing"
                  @click="purchaseItem(item)"
                >
                  <span class="coin-icon">🪙</span>
                  {{ item.price }}
                </button>
              </template>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Notification -->
      <Transition name="fade">
        <div v-if="notification" class="notification">
          {{ notification }}
        </div>
      </Transition>
    </div>
  </div>
</template>

<style scoped>
.store-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;
}

.store-modal {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border-radius: 24px;
  width: 100%;
  max-width: 900px;
  max-height: 90vh;
  overflow: hidden;
  border: 1px solid rgba(255,215,0,0.3);
  box-shadow: 0 0 50px rgba(138,43,226,0.3);
  position: relative;
}

/* Header */
.store-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  background: rgba(0,0,0,0.3);
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.header-left h2 {
  margin: 0;
  font-size: 1.5rem;
}

.elite-badge {
  background: linear-gradient(135deg, #8a2be2 0%, #ffd700 100%);
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.coins-display {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(255,215,0,0.1);
  padding: 0.5rem 1rem;
  border-radius: 20px;
  border: 1px solid rgba(255,215,0,0.3);
}

.coin-icon {
  font-size: 1.2rem;
}

.coin-amount {
  font-weight: 700;
  color: #ffd700;
}

.close-btn {
  background: rgba(255,255,255,0.1);
  border: none;
  color: white;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  cursor: pointer;
  font-size: 1.2rem;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(255,68,68,0.3);
}

/* Not Elite Warning */
.not-elite-warning {
  padding: 4rem 2rem;
  text-align: center;
}

.not-elite-warning p {
  font-size: 1.2rem;
  color: #888;
  margin-bottom: 1.5rem;
}

.upgrade-link {
  display: inline-block;
  background: linear-gradient(135deg, #8a2be2 0%, #ffd700 100%);
  color: white;
  padding: 1rem 2rem;
  border-radius: 10px;
  text-decoration: none;
  font-weight: 600;
  transition: all 0.3s;
}

.upgrade-link:hover {
  transform: scale(1.05);
}

/* Store Content */
.store-content {
  padding: 1.5rem 2rem;
  max-height: calc(90vh - 100px);
  overflow-y: auto;
}

/* Categories */
.categories {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  overflow-x: auto;
  padding-bottom: 0.5rem;
}

.category-btn {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  color: #888;
  padding: 0.75rem 1.25rem;
  border-radius: 10px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}

.category-btn:hover {
  background: rgba(255,255,255,0.1);
  color: white;
}

.category-btn.active {
  background: linear-gradient(135deg, #ffd700 0%, #ff8c00 100%);
  color: #000;
  border-color: transparent;
}

/* Items Grid */
.items-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1rem;
}

/* Item Card */
.item-card {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 16px;
  padding: 1.25rem;
  position: relative;
  overflow: hidden;
  transition: all 0.3s;
}

.item-card:hover {
  transform: translateY(-3px);
  border-color: rgba(255,215,0,0.3);
}

.item-card.owned {
  border-color: rgba(0,200,83,0.3);
}

.item-card.equipped {
  border-color: #ffd700;
  box-shadow: 0 0 20px rgba(255,215,0,0.2);
}

.rarity-bar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
}

/* Preview */
.item-preview {
  font-size: 3rem;
  text-align: center;
  padding: 1rem 0;
}

.color-preview {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  margin: 0 auto;
}

/* Info */
.item-info {
  text-align: center;
  margin-bottom: 1rem;
}

.item-info h4 {
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
}

.item-info p {
  margin: 0;
  color: #888;
  font-size: 0.85rem;
}

.rarity-tag {
  font-size: 0.7rem;
  font-weight: 600;
  margin-top: 0.5rem;
}

/* Actions */
.item-actions {
  display: flex;
  justify-content: center;
}

.btn-buy {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: linear-gradient(135deg, #ffd700 0%, #ff8c00 100%);
  color: #000;
  font-weight: 600;
  padding: 0.5rem 1.5rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-buy:hover:not(:disabled) {
  transform: scale(1.05);
}

.btn-buy:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-equip {
  background: rgba(0,200,83,0.2);
  color: #00c853;
  border: 1px solid rgba(0,200,83,0.3);
  padding: 0.5rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
}

.btn-equip:hover {
  background: rgba(0,200,83,0.3);
}

.btn-unequip {
  background: rgba(255,215,0,0.2);
  color: #ffd700;
  border: 1px solid rgba(255,215,0,0.3);
  padding: 0.5rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
}

/* Notification */
.notification {
  position: absolute;
  bottom: 1rem;
  left: 50%;
  transform: translateX(-50%);
  background: linear-gradient(135deg, #00c853 0%, #00e676 100%);
  color: #000;
  padding: 0.75rem 1.5rem;
  border-radius: 10px;
  font-weight: 600;
  box-shadow: 0 5px 20px rgba(0,0,0,0.3);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(10px);
}

/* Responsive */
@media (max-width: 768px) {
  .store-modal {
    max-height: 100vh;
    border-radius: 0;
  }
  
  .store-header {
    flex-direction: column;
    gap: 1rem;
  }
  
  .items-grid {
    grid-template-columns: 1fr;
  }
}
</style>
