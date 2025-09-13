<script setup>
import { onMounted, onBeforeUnmount, watch, computed, ref } from 'vue'
import SideMenu from '@/components/SideMenu.vue'
import { useAuth } from '@/stores/useAuth'
import { useUnread } from '@/stores/useUnread'

const auth   = useAuth()
const unread = useUnread()
const showMenu = ref(false)

onMounted(() => { if (auth.isAuthed) unread.startPolling(8000) })
watch(() => auth.isAuthed, v => { v ? unread.startPolling(8000) : unread.stopPolling() })
onBeforeUnmount(() => unread.stopPolling())

const unreadText = computed(() => unread.count > 99 ? '99+' : String(unread.count))
</script>

<template>
  <footer class="app-footer-fixed position-fixed w-100 bg-white bottom-0" style="border-top: 1px lightgray solid;">
    <ul class="container m-auto d-flex justify-content-around align-items-center p-3 text-primary">
      <li>
        <router-link to="/mypage" class="text-primary" aria-label="マイページ">
          <IconHome :size="24" />
        </router-link>
      </li>

      <li>
        <router-link to="/search" class="text-primary" aria-label="ユーザー検索">
          <IconSearch :size="24" />
        </router-link>
      </li>

      <li class="position-relative">
        <router-link to="/chats" class="text-primary d-inline-block position-relative" aria-label="チャット">
          <IconMessages :size="24" />
          <span
            v-if="unread.count"
            class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger"
            style="font-size:.7rem; min-width:1.25rem;"
          >
            {{ unreadText }}
          </span>
        </router-link>
      </li>

      <li>
        <button
          class="d-inline-flex align-items-center gap-2 border-0 bg-transparent"
          type="button"
          aria-label="メニュー"
          @click="showMenu = true"
        >
          <IconMenu2 :size="24" :stroke="2" class="text-primary"/>
        </button>
        <SideMenu v-model="showMenu" />
      </li>
    </ul>
  </footer>
</template>

<style scoped>
.footer-nav{position:sticky;bottom:0;background:#fff;border-top:1px solid #eee}
.icon{display:inline-flex;align-items:center;justify-content:center;width:64px;height:52px}
</style>
