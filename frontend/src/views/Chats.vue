<!-- src/views/Chats.vue -->
<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { fetchChats, fetchMe } from '@/api'
import { useUnread } from '@/stores/useUnread'
import { useUser } from '@/stores/useUser'
import Avatar from '@/components/Avatar.vue'

const router = useRouter()
const unread = useUnread()
const userStore = useUser()
const meLocal = ref(null)   // store未読込時の保険

const loading = ref(true)
const err = ref('')
const threads = ref([])
const page = ref(1)
const hasNext = ref(false)

/* 視聴者がLCIQ登録済みか（画像 or スコア どちらかがあればOK） */
const viewerHasLciq = computed(() => {
  const me = userStore?.me || meLocal.value || {}
  const hasImg = !!me.lciq_image_url
  const hasScore = me.lciq_score !== null && me.lciq_score !== undefined && String(me.lciq_score) !== ''
  return hasImg || hasScore
})

async function load(p = 1) {
  loading.value = true
  err.value = ''
  try {
    const data = await fetchChats(p)
    const rows = Array.isArray(data) ? data : (data.results || data.items || [])
    rows.sort((a, b) => {
      const at = new Date(a.updated_at || a.last_message?.created_at || 0)
      const bt = new Date(b.updated_at || b.last_message?.created_at || 0)
      return bt - at
    })
    threads.value = p === 1 ? rows : [...threads.value, ...rows]
    hasNext.value = !!data?.next
    page.value = p
  } catch (e) {
    err.value = '読み込みに失敗しました'
    console.error('[Chats]', e?.response?.status, e?.response?.data || e)
  } finally {
    loading.value = false
  }
}

function more(){ if (hasNext.value) load(page.value + 1) }

/* クリック時ガード：LCIQ未登録ならアラート→マイページへ */
async function openThread(id){
  if (!viewerHasLciq.value) {
    alert('メッセージ機能を使うには、まずLCIQを登録してください。マイページから登録できます。')
    router.push('/mypage')   // 必要なら '/profile/edit' に変更可
    return
  }
  try { await unread.readThread(Number(id)) } catch {}
  router.push('/chats/' + id)
}

onMounted(async () => {
  // storeに me が無ければ一度だけ取得（保険）
  if (!userStore?.me) {
    try { meLocal.value = await fetchMe() } catch {}
  }
  await unread.refresh()
  await load(1)
})
</script>

<template>
  <div class="wrap">
    <div class="h2 fw-bold my-3">メッセージ</div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border" role="status"></div>
    </div>
    <div v-else-if="err" class="alert alert-danger">{{ err }}</div>
    <div v-else-if="threads.length === 0" class="text-center text-muted py-5">
      出会いはすぐそこに。
    </div>

    <div v-else class="d-flex flex-column gap-3">
      <a
        v-for="t in threads"
        :key="t.partner?.id || t.user?.id"
        class="position-relative"
        @click="openThread(t.partner?.id || t.user?.id)"
        style="cursor:pointer"
      >
        <div class="d-flex align-items-center gap-3">
          <!-- ▼ LCIQ未登録なら相手アバターをブラー -->
          <div class="avatar-wrap" :class="{ 'lciq-blur': !viewerHasLciq }">
            <Avatar :src="$avatar.user(t.partner || t.user)" :size="44" />
          </div>

          <div class="flex-fill">
            <div
              class="name"
              :class="{'fw-bold': unread.of(t.partner?.id || t.user?.id)}"
            >
              {{ (t.partner || t.user)?.nickname || (t.partner || t.user)?.username || '???' }}
            </div>
            <div
              class="text-muted small text-truncate"
              :class="{'fw-bold': unread.of(t.partner?.id || t.user?.id)}"
            >
              {{ t.last_message?.text || t.preview || '…' }}
            </div>
          </div>

          <div class="text-end">
            <small class="text-nowrap text-muted d-block">
              {{ (t.updated_at || t.last_message?.created_at || '').slice(0,16).replace('T',' ') }}
            </small>
            <span
              v-if="unread.of(t.partner?.id || t.user?.id)"
              class="badge bg-danger mt-1"
            >
              {{ unread.of(t.partner?.id || t.user?.id) > 99 ? '99+' : unread.of(t.partner?.id || t.user?.id) }}
            </span>
          </div>
        </div>
      </a>

      <div class="text-center mt-3" v-if="hasNext">
        <button class="btn btn-outline-primary" @click="more">もっと見る</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Avatarのimgにブラー適用（Avatarは内部でimgを描く想定） */
.avatar-wrap :deep(img){
  transition: filter .2s ease, transform .2s ease;
}
.avatar-wrap.lciq-blur :deep(img){
  filter: blur(10px) saturate(.9);
  transform: scale(1.02);
}
</style>
