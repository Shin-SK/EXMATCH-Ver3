<script setup>
import { useUnread } from '@/stores/useUnread'

const unread = useUnread()
</script>

<template>
  <header class="hdr">
    <nav class="nav">
      <router-link to="/mypage">MyPage</router-link>
      <router-link to="/matches">Matches</router-link>
      <router-link to="/chats" class="rel">
        Chats
        <span v-if="unread.count>0" class="badge">{{ unread.count }}</span>
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
