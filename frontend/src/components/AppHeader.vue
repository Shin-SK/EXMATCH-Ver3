<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { fetchUnread } from '@/api'

const unread = ref(0)
let timer = null

async function loadUnread(){
  try {
    const d = await fetchUnread()
    unread.value = d?.count ?? d?.unread ?? (Array.isArray(d) ? d.length : 0)
  } catch {}
}

onMounted(() => {
  loadUnread()
  timer = setInterval(loadUnread, 30000)
})
onUnmounted(() => timer && clearInterval(timer))
</script>

<template>
  <header class="hdr">
    <nav class="nav">
      <router-link to="/mypage">MyPage</router-link>
      <router-link to="/matches">Matches</router-link>
      <router-link to="/chats" class="rel">
        Chats
        <span v-if="unread>0" class="badge">{{ unread }}</span>
      </router-link>
    </nav>
  </header>
</template>

<style scoped>
.hdr{padding:10px 14px;border-bottom:1px solid #eee;background:#fff;position:sticky;top:0;z-index:10}
.nav{display:flex;gap:14px;align-items:center}
.rel{position:relative}
.badge{position:absolute;top:-6px;right:-12px;padding:2px 6px;border-radius:999px;background:#f33;color:#fff;font-size:12px;line-height:1}
</style>
