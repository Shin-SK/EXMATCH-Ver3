<!-- src/views/LikesReceived.vue -->
<script setup>
import { ref, onMounted } from 'vue'
import { fetchLikesReceived } from '@/api'
import UserCardMini from '@/components/UserCardMini.vue'

const loading = ref(true)
const err = ref('')
const rows = ref([])
const page = ref(1)
const hasNext = ref(false)

async function load(p = 1) {
	loading.value = true
	err.value = ''
	try {
		const d = await fetchLikesReceived(p)
		const list = Array.isArray(d) ? d : (d.results || [])
		rows.value = p === 1 ? list : [...rows.value, ...list]
		hasNext.value = !!d?.next
		page.value = p
	} catch (e) {
		err.value = '読み込みに失敗しました'
		console.error('[LikesReceived]', e?.response?.status, e?.response?.data || e)
	} finally {
		loading.value = false
	}
}
function more(){ if(hasNext.value) load(page.value + 1) }

onMounted(() => load(1))
</script>

<template>
  <div class="py-3">
    <div class="head-set">
      <h2>LIKE</h2>
      <h3>もらったいいね</h3>
    </div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border" role="status"></div>
    </div>
    <div v-else-if="err" class="alert alert-danger">{{ err }}</div>
    <div v-else-if="rows.length === 0" class="text-center text-muted py-5">
      出会いはすぐそこに。
    </div>

    <div v-else class="feed feed-mini">
      <UserCardMini
        v-for="it in rows"
        :key="it.id"
        :user="it.from_user"
        :created-at="it.created_at"
        :link-to="`/users/${it.from_user?.id}`"
      />
      <div class="text-center mt-3" v-if="hasNext">
        <button class="btn btn-outline-primary" @click="more">もっと見る</button>
      </div>
    </div>
  </div>
</template>
