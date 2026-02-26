<!-- src/views/Matches.vue（新規 or 差し替え） -->
<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchMatches, unmatchUser } from '@/api'
import { useUnread } from '@/stores/useUnread'
import Avatar from '@/components/Avatar.vue'

const router = useRouter()
const unread = useUnread()

const loading = ref(true)
const err = ref('')
const rows = ref([])
const page = ref(1)
const hasNext = ref(false)

async function load(p=1){
  loading.value = true
  err.value = ''
  try{
    const data = await fetchMatches(p)
    const list = Array.isArray(data) ? data : (data.results || [])
    rows.value = p===1 ? list : [...rows.value, ...list]
    hasNext.value = !!data?.next
    page.value = p
  }catch(e){
    err.value = '読み込みに失敗しました'
    console.error('[Matches]', e?.response?.status, e?.response?.data || e)
  }finally{
    loading.value = false
  }
}

function toChat(uid){
  router.push(`/chats/${uid}`)
}

async function doUnmatch(uid){
  if(!confirm('この相手とのマッチを解除します。よろしいですか？')) return
  try{
    await unmatchUser(uid)
    rows.value = rows.value.filter(r => (r.partner?.id || r.user?.id) !== uid)
  }catch(e){
    alert('解除に失敗しました')
    console.error('[Unmatch]', e?.response?.status, e?.response?.data || e)
  }
}

function more(){ if(hasNext.value) load(page.value+1) }

onMounted(async () => {
  await unread.refresh()
  await load(1)
})
</script>

<template>
  <div class="py-3">
    <div class="h2 fw-bold my-3">マッチした人</div>


    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border" role="status"></div>
    </div>
    <div v-else-if="err" class="alert alert-danger">{{ err }}</div>

    <div v-else class="list-group">
      <div
        v-for="m in rows"
        :key="m.id"
        class="list-group-item list-group-item-action"
      >
        <div class="d-flex align-items-center gap-3">
          <Avatar :src="$avatar.user(m.partner || m.user)" :size="44" />
          <div class="flex-fill">
            <div class="d-flex align-items-center gap-2">
              <strong>{{ (m.partner || m.user)?.nickname || (m.partner || m.user)?.username || '???' }}</strong>
              <span
                v-if="unread.of((m.partner?.id || m.user?.id))"
                class="badge bg-danger"
              >
                {{ unread.of((m.partner?.id || m.user?.id)) > 99 ? '99+' : unread.of((m.partner?.id || m.user?.id)) }}
              </span>
            </div>
            <small class="text-muted">matched at {{ (m.created_at || '').slice(0,16).replace('T',' ') }}</small>
          </div>

          <div class="d-flex gap-2">
            <button class="btn btn-sm btn-primary" @click="toChat(m.partner?.id || m.user?.id)">
              チャット
            </button>
            <button class="btn btn-sm btn-outline-danger" @click="doUnmatch(m.partner?.id || m.user?.id)">
              解除
            </button>
          </div>
        </div>
      </div>

      <div class="text-center mt-3" v-if="hasNext">
        <button class="btn btn-outline-primary" @click="more">もっと見る</button>
      </div>
    </div>
  </div>
</template>
