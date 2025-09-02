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
  <div class="app-shell">
    <!-- Loader -->
    <div class="loader-overlay" :class="{ hide: loaded }">
      <div class="spinner-border" role="status" aria-label="loading"></div>
    </div>

    <!-- <header class="main-header">
      <nav class="nav p-3 w-100 d-flex align-items-center justify-content-between">
        <router-link to="/mypage" class="logo d-flex align-items-center gap-2">
          <img src="/img/logo.svg" alt="logo" style="height: 40px; width: auto;">
        </router-link>
        <div class="links d-flex align-items-center gap-3">
          <router-link to="/mypage">マイページ</router-link>
          <router-link to="/users">検索</router-link>
          <router-link to="/chats">メッセージ</router-link>
          <router-link to="/profile/edit">設定</router-link>
        </div>
      </nav>
    </header> -->

    <!-- メイン -->
    <main class="container main-scroll">
        <router-view />
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
