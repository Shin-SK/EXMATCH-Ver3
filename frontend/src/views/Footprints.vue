<!-- src/views/Footprints.vue（新規） -->
<script setup>
import { ref, onMounted } from 'vue'
import { fetchFootprints } from '@/api'
import UserCardMini from '@/components/UserCardMini.vue'

const loading = ref(true)
const err = ref('')
const rows = ref([])
const page = ref(1)
const hasNext = ref(false)

async function load(p=1){
  loading.value = true
  err.value = ''
  try{
    const d = await fetchFootprints(p)
    const list = Array.isArray(d) ? d : (d.results || d.items || [])
    rows.value = p===1 ? list : [...rows.value, ...list]
    hasNext.value = !!d?.next
    page.value = p
  }catch(e){
    err.value = '読み込みに失敗しました'
    console.error('[Footprints]', e?.response?.status, e?.response?.data || e)
  }finally{
    loading.value = false
  }
}
function more(){ if(hasNext.value) load(page.value+1) }

onMounted(() => load(1))
</script>

<template>
  <div class="py-3">
    <h1 class="h2 fw-bold my-3">あしあと</h1>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border" role="status"></div>
    </div>
    <div v-else-if="err" class="alert alert-danger">{{ err }}</div>

    <div v-else class="feed feed-mini">
      <template v-if="rows.length">
        <UserCardMini
          v-for="fp in rows"
          :key="fp.id"
          :user="fp.from_user"
          :created-at="fp.created_at"
          :link-to="`/users/${fp.from_user?.id}`"
        />
        <div class="text-center mt-3" v-if="hasNext">
          <button class="btn btn-outline-primary" @click="more">もっと見る</button>
        </div>
      </template>
      <div v-else class="text-center text-muted py-5">まだ足跡はありません</div>
    </div>
  </div>
</template>
