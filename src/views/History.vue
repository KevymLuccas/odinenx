<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="history-page">
    <div class="page-header">
      <button @click="router.push('/dashboard')" class="back-btn">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
        Voltar
      </button>
      <h1>Histórico</h1>
      <p>Suas análises e operações anteriores</p>
    </div>

    <div class="empty-state">
      <div class="icon-wrapper">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M12 8v4l3 3"/>
          <circle cx="12" cy="12" r="10"/>
        </svg>
      </div>
      <h2>Histórico vazio</h2>
      <p>Suas análises e operações aparecerão aqui.</p>
    </div>
  </div>
</template>

<style scoped>
.history-page {
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

.empty-state {
  max-width: 500px;
  margin: 0 auto;
  text-align: center;
  padding: 80px 40px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
}

.icon-wrapper {
  width: 100px;
  height: 100px;
  background: rgba(234, 179, 8, 0.15);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 30px;
}

.icon-wrapper svg {
  width: 50px;
  height: 50px;
  stroke: #eab308;
}

.empty-state h2 {
  font-size: 1.5rem;
  margin-bottom: 10px;
}

.empty-state p {
  color: rgba(255, 255, 255, 0.5);
}
</style>
