<!-- src/components/SideMenu.vue -->
<script setup>
import { onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'   // ★ 追加
import { api } from '@/api'                         // ★ 追加
import { useAuth } from '@/stores/useAuth'          // ★ 追加
import Offcanvas from 'bootstrap/js/dist/offcanvas'

let inst = null
const route = useRoute()
const router = useRouter()          // ★ 追加
const auth = useAuth()              // ★ 追加

onMounted(() => {
  const el = document.getElementById('mainMenu')
  inst = Offcanvas.getOrCreateInstance(el, { scroll: true, backdrop: true })
})
onUnmounted(() => { inst = null })

watch(() => route.fullPath, () => inst?.hide())

async function doLogout() {
  try { await api.post('auth/logout/') } catch (_) {}
  try { localStorage.removeItem('token') } catch (_) {}
  // axiosの既定ヘッダを念のためクリア
  if (api?.defaults?.headers?.common) delete api.defaults.headers.common.Authorization
  // store側も軽くリセット（メソッドがあるなら置き換えてOK）
  try {
    auth.token = ''
    auth.user = null
  } catch (_) {}

  inst?.hide()
  router.replace('/home')
}
</script>

<template>
  <div class="offcanvas offcanvas-start" tabindex="-1" id="mainMenu" aria-labelledby="mainMenuLabel">
    <div class="offcanvas-header">
      <button type="button" class="btn-close" data-bs-dismiss="offcanvas" aria-label="閉じる"></button>
    </div>

    <div class="offcanvas-body d-flex flex-column justify-content-between gap-2 pt-5">
      <div class="wrap d-flex flex-column gap-5">
        <router-link to="/mypage" data-bs-dismiss="offcanvas">マイページ<IconChevronRight :size="16" /></router-link>
        <router-link to="/users"   data-bs-dismiss="offcanvas">検索<IconChevronRight :size="16" /></router-link>
        <router-link to="/chats"   data-bs-dismiss="offcanvas">メッセージ<IconChevronRight :size="16" /></router-link>
        <router-link to="/profile/edit" data-bs-dismiss="offcanvas">設定<IconChevronRight :size="16" /></router-link>
      </div>

      <!-- ★ a href="#" はやめて button に -->
      <div class="logout" style="text-align:center; color: lightgray;">
        <button type="button" class="btn btn-outline-danger w-100" @click="doLogout">
          ログアウト
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
/* 必要なら幅調整（デフォ: 400px） */
.offcanvas{ width: 80vw; }

.offcanvas-body{
  .wrap{
    a{
      border-bottom: 1px dotted lightgray;
      display: flex;
      width: 100%;
      justify-content: space-between;
    }
  }
}

</style>
