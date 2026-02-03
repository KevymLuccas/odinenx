<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  show: Boolean,
  type: { type: String, default: 'success' },
  title: String,
  message: String,
  duration: { type: Number, default: 5000 }
})

const emit = defineEmits(['close'])
const visible = ref(false)

watch(() => props.show, (newVal) => {
  if (newVal) {
    visible.value = true
    if (props.duration > 0) {
      setTimeout(() => {
        visible.value = false
        emit('close')
      }, props.duration)
    }
  } else {
    visible.value = false
  }
}, { immediate: true })

const close = () => {
  visible.value = false
  emit('close')
}

const icons = {
  success: '✓',
  error: '✗',
  info: 'ℹ',
  warning: '⚠',
  welcome: '👋',
  payment: '💳',
  beta: '🚀'
}
</script>

<template>
  <Teleport to="body">
    <Transition name="toast">
      <div v-if="visible" class="toast-overlay" @click.self="close">
        <div :class="['toast-container', type]">
          <div class="toast-icon">{{ icons[type] || icons.info }}</div>
          <div class="toast-content">
            <h3 class="toast-title">{{ title }}</h3>
            <p class="toast-message">{{ message }}</p>
          </div>
          <button class="toast-close" @click="close">×</button>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.toast-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 100px;
  z-index: 10000;
  background: rgba(0, 0, 0, 0.3);
  -webkit-backdrop-filter: blur(4px);
  backdrop-filter: blur(4px);
}

.toast-container {
  background: linear-gradient(135deg, #1a1a1a, #0a0a0a);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 16px;
  padding: 24px 30px;
  display: flex;
  align-items: flex-start;
  gap: 16px;
  max-width: 420px;
  width: 90%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  animation: slideIn 0.4s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-30px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.toast-icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  flex-shrink: 0;
}

.toast-container.success .toast-icon {
  background: rgba(76, 175, 80, 0.2);
  color: #4caf50;
}

.toast-container.error .toast-icon {
  background: rgba(244, 67, 54, 0.2);
  color: #f44336;
}

.toast-container.info .toast-icon {
  background: rgba(33, 150, 243, 0.2);
  color: #2196f3;
}

.toast-container.warning .toast-icon {
  background: rgba(255, 193, 7, 0.2);
  color: #ffc107;
}

.toast-container.welcome .toast-icon {
  background: rgba(156, 39, 176, 0.2);
  color: #9c27b0;
}

.toast-container.payment .toast-icon {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.2), rgba(0, 200, 83, 0.2));
  color: #00c853;
}

.toast-container.beta .toast-icon {
  background: rgba(255, 152, 0, 0.2);
  color: #ff9800;
}

.toast-content {
  flex: 1;
}

.toast-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #fff;
  margin-bottom: 6px;
}

.toast-message {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.5;
}

.toast-close {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.5);
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.toast-close:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}
</style>
