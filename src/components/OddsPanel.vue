<script setup>
/**
 * 🎯 OddsPanel.vue - Painel de Odds
 * ODINENX v2.0
 */

import { ref, computed } from 'vue'

const props = defineProps({
  room: {
    type: Object,
    required: true
  },
  selectedOdds: {
    type: Array,
    default: () => []
  },
  userOdds: {
    type: Array,
    default: () => []
  },
  mode: {
    type: String,
    default: 'view' // 'select' ou 'view'
  }
})

const emit = defineEmits(['update:selectedOdds'])

// Odds padrão para seleção do usuário (categorias fixas, valores ilustrativos)
const availableOdds = computed(() => [
  {
    category: '1x2 - Resultado Final',
    options: [
      { type: '1x2', pick: 'home', label: props.room?.home_team || 'Casa', value: 1.85 },
      { type: '1x2', pick: 'draw', label: 'Empate', value: 3.40 },
      { type: '1x2', pick: 'away', label: props.room?.away_team || 'Fora', value: 4.20 }
    ]
  },
  {
    category: 'Gols - Over/Under',
    options: [
      { type: 'over_under', pick: 'over_1.5', label: 'Mais de 1.5', value: 1.35 },
      { type: 'over_under', pick: 'over_2.5', label: 'Mais de 2.5', value: 1.90 },
      { type: 'over_under', pick: 'under_2.5', label: 'Menos de 2.5', value: 1.95 }
    ]
  },
  {
    category: 'Ambas Marcam',
    options: [
      { type: 'btts', pick: 'yes', label: 'Sim', value: 1.75 },
      { type: 'btts', pick: 'no', label: 'Não', value: 2.05 }
    ]
  },
  {
    category: 'Dupla Chance',
    options: [
      { type: 'double_chance', pick: '1x', label: `${props.room?.home_team || 'Casa'} ou Empate`, value: 1.25 },
      { type: 'double_chance', pick: '12', label: `${props.room?.home_team || 'Casa'} ou ${props.room?.away_team || 'Fora'}`, value: 1.15 },
      { type: 'double_chance', pick: 'x2', label: `${props.room?.away_team || 'Fora'} ou Empate`, value: 1.55 }
    ]
  }
])

// Verificar se odd está selecionada
function isSelected(odd) {
  return props.selectedOdds.some(
    s => s.type === odd.type && s.pick === odd.pick
  )
}

// Toggle seleção
function toggleOdd(odd) {
  if (props.mode !== 'select') return
  
  const current = [...props.selectedOdds]
  const idx = current.findIndex(s => s.type === odd.type && s.pick === odd.pick)
  
  if (idx >= 0) {
    current.splice(idx, 1)
  } else {
    // Remover outras seleções do mesmo tipo
    const filtered = current.filter(s => s.type !== odd.type)
    filtered.push(odd)
    emit('update:selectedOdds', filtered)
    return
  }
  
  emit('update:selectedOdds', current)
}

// Obter status da odd do usuário
function getOddStatus(odd) {
  const userOdd = props.userOdds.find(
    o => o.odd_type === odd.type && o.odd_pick === odd.pick
  )
  return userOdd?.status || null
}

// Classes de status
function getStatusClass(odd) {
  const status = getOddStatus(odd)
  return {
    pending: status === 'pending',
    won: status === 'won',
    lost: status === 'lost'
  }
}
</script>

<template>
  <div class="odds-panel">
    <!-- Modo Seleção -->
    <template v-if="mode === 'select'">
      <div 
        v-for="category in availableOdds" 
        :key="category.category"
        class="odds-category"
      >
        <h4 class="category-title">{{ category.category }}</h4>
        <div class="odds-grid">
          <button
            v-for="odd in category.options"
            :key="`${odd.type}-${odd.pick}`"
            class="odd-btn"
            :class="{ selected: isSelected(odd) }"
            @click="toggleOdd(odd)"
          >
            <span class="odd-label">{{ odd.label }}</span>
            <span class="odd-value">{{ odd.value.toFixed(2) }}</span>
          </button>
        </div>
      </div>
      
      <!-- Resumo da seleção -->
      <div class="selection-summary" v-if="selectedOdds.length > 0">
        <h4>📋 Selecionados ({{ selectedOdds.length }})</h4>
        <div class="selected-list">
          <div 
            v-for="odd in selectedOdds" 
            :key="`sel-${odd.type}-${odd.pick}`"
            class="selected-item"
          >
            <span>{{ odd.label }}</span>
            <span class="odd-value">{{ odd.value.toFixed(2) }}</span>
            <button class="remove-btn" @click="toggleOdd(odd)">×</button>
          </div>
        </div>
      </div>
    </template>
    
    <!-- Modo Visualização -->
    <template v-else>
      <div class="user-odds-list">
        <div 
          v-for="odd in userOdds" 
          :key="odd.id"
          class="user-odd-item"
          :class="getStatusClass({ type: odd.odd_type, pick: odd.odd_pick })"
        >
          <div class="odd-info">
            <span class="odd-type">{{ odd.odd_type }}</span>
            <span class="odd-pick">{{ odd.odd_pick }}</span>
          </div>
          <div class="odd-value-display">
            <span class="value">{{ parseFloat(odd.odd_value).toFixed(2) }}</span>
            <span class="status-icon">
              <template v-if="odd.status === 'pending'">⏳</template>
              <template v-else-if="odd.status === 'won'">✅</template>
              <template v-else-if="odd.status === 'lost'">❌</template>
            </span>
          </div>
        </div>
      </div>
      
      <div v-if="userOdds.length === 0" class="no-odds">
        <p>Nenhuma odd selecionada</p>
      </div>
    </template>
  </div>
</template>

<style scoped>
.odds-panel {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* Category */
.odds-category {
  background: rgba(255,255,255,0.05);
  border-radius: 12px;
  padding: 1rem;
}

.category-title {
  font-size: 0.85rem;
  color: #888;
  margin: 0 0 0.75rem 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Odds Grid */
.odds-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
  gap: 0.5rem;
}

/* Odd Button */
.odd-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  padding: 0.75rem 0.5rem;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px;
  background: rgba(255,255,255,0.05);
  color: white;
  cursor: pointer;
  transition: all 0.2s;
}

.odd-btn:hover {
  border-color: rgba(255,215,0,0.5);
  background: rgba(255,215,0,0.1);
}

.odd-btn.selected {
  border-color: #ffd700;
  background: rgba(255,215,0,0.2);
}

.odd-label {
  font-size: 0.8rem;
  color: #ccc;
  text-align: center;
}

.odd-value {
  font-size: 1.1rem;
  font-weight: 700;
  color: #ffd700;
}

/* Selection Summary */
.selection-summary {
  background: rgba(255,215,0,0.1);
  border: 1px solid rgba(255,215,0,0.3);
  border-radius: 12px;
  padding: 1rem;
}

.selection-summary h4 {
  margin: 0 0 0.75rem 0;
  font-size: 0.9rem;
}

.selected-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.selected-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  background: rgba(0,0,0,0.2);
  border-radius: 8px;
}

.selected-item span:first-child {
  flex: 1;
  font-size: 0.85rem;
}

.remove-btn {
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 50%;
  background: rgba(255,0,0,0.3);
  color: white;
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
}

.remove-btn:hover {
  background: rgba(255,0,0,0.5);
}

/* User Odds List (View Mode) */
.user-odds-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.user-odd-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  border-radius: 10px;
  background: rgba(255,255,255,0.05);
  border-left: 3px solid transparent;
  transition: all 0.3s;
}

.user-odd-item.pending {
  border-left-color: #ffc107;
}

.user-odd-item.won {
  border-left-color: #28a745;
  background: rgba(40,167,69,0.15);
}

.user-odd-item.lost {
  border-left-color: #dc3545;
  background: rgba(220,53,69,0.15);
  opacity: 0.7;
}

.odd-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.odd-type {
  font-size: 0.75rem;
  color: #888;
  text-transform: uppercase;
}

.odd-pick {
  font-size: 0.9rem;
  font-weight: 600;
}

.odd-value-display {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.odd-value-display .value {
  font-size: 1.1rem;
  font-weight: 700;
  color: #ffd700;
}

.status-icon {
  font-size: 1.2rem;
}

.no-odds {
  text-align: center;
  color: #666;
  padding: 1rem;
}
</style>
