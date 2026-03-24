<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import FooterNav from '@/components/FooterNav.vue'

const loaded = ref(false)
let t = null

onMounted(() => {
  // ローダをフェードアウト
  t = setTimeout(() => { loaded.value = true }, 50)
})
onUnmounted(() => { if (t) clearTimeout(t) })
</script>

<template>
  <div class="app-shell bg-light-subtle">
    <!-- Loader -->
    <div class="loader-overlay" :class="{ hide: loaded }">
      <div class="spinner-border" role="status" aria-label="loading"></div>
    </div>

    <!-- メイン -->
    <main class="main-scroll">
      <div class="container">
        <router-view />
      </div>
    </main>

    <!-- フッター -->
    <FooterNav />
  </div>
</template>

<style scoped>
.loader-overlay{
  position:fixed; inset:0; display:flex; align-items:center; justify-content:center;
  background:#fff; z-index:2000; opacity:1; transition:opacity .4s ease;
}
.loader-overlay.hide{ opacity:0; pointer-events:none }
</style>
