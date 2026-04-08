<!-- src/views/LikesSent.vue（新規） -->
<script setup>
import { ref, onMounted } from 'vue'
import { fetchLikesSent } from '@/api'
import UserCardMini from '@/components/UserCardMini.vue'

const loading = ref(true)
const err = ref('')
const rows = ref([])
const page = ref(1)
const hasNext = ref(false)

async function load(p=1){
  loading.value = true; err.value = ''
  try{
    const d = await fetchLikesSent(p)
    const list = Array.isArray(d) ? d : (d.results || d.items || [])
    rows.value = p===1 ? list : [...rows.value, ...list]
    hasNext.value = !!d?.next
    page.value = p
  }catch(e){
    err.value = '読み込みに失敗しました'
    console.error('[LikesSent]', e?.response?.status, e?.response?.data || e)
  }finally{
    loading.value = false
  }
}
function more(){ if(hasNext.value) load(page.value+1) }

onMounted(() => load(1))
</script>

<template>
  <div class="py-3">
    <div class="head-set">
      <h2>LIKE</h2>
      <h3>送ったいいね</h3>
    </div>

    <div v-if="loading" class="text-center py-5"><div class="spinner-border" role="status"></div></div>
    <div v-else-if="err" class="alert alert-danger">{{ err }}</div>

    <div v-else class="feed feed-mini">
      <UserCardMini
        v-for="it in rows"
        :key="it.id"
        :user="it.to_user"
        :created-at="it.created_at"
        :link-to="`/users/${it.to_user?.id}`"
      />
      <div class="text-center mt-3" v-if="hasNext">
        <button class="btn btn-outline-primary" @click="more">もっと見る</button>
      </div>
    </div>
  </div>
</template>
