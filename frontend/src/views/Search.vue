<script setup>
import { ref, reactive, onMounted } from 'vue'
import { fetchProfiles, fetchMatches, likeUser } from '@/api'
import UserCard from '@/components/UserCard.vue'
import SearchSidebar from '@/components/SearchSidebar.vue'
import { IconAdjustmentsHorizontal } from '@tabler/icons-vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const f = reactive({
	radius:'', lat:'', lon:'',
	q:'', gender:'', plan:'',
	has_image:false, verified:false,
	age_min:'', age_max:'', area:'',
})

const showSidebar = ref(false)
const loading = ref(true)
const err = ref('')
const items = ref([])
const page = ref(1)
const hasNext = ref(false)
const matchedSet = ref(new Set())

function toGeoParams(){ return { radius:f.radius||undefined, lat:f.lat||undefined, lon:f.lon||undefined } }
function toDetailParams(){ return {
	q:f.q||undefined, gender:f.gender||undefined, plan:f.plan||undefined,
	has_image: f.has_image ? '1' : undefined, verified: f.verified ? '1' : undefined,
	age_min:f.age_min||undefined, age_max:f.age_max||undefined, area:f.area||undefined
} }

async function load(params, p=1){
	loading.value = true; 
  err.value=''
	try{
		const d = await fetchProfiles(params, p)
		const rows = Array.isArray(d) ? d : (d.results || d.items || [])
		items.value = p===1 ? rows : [...items.value, ...rows]
		hasNext.value = !!d?.next
		page.value = p
	}catch(e){
		err.value = '読み込みに失敗しました'
		console.error('[Search]', e?.response?.status, e?.response?.data || e)
	}finally{
		loading.value = false
	}
}
const more = () => { if (hasNext.value) load(currentParams.value, page.value+1) }

const currentParams = ref({})
async function onGeoSearch(){ currentParams.value = toGeoParams(); 
  await load(currentParams.value, 1) }
async function onDetailSearch(){ currentParams.value = toDetailParams(); 
  await load(currentParams.value, 1) }
function onReset(){
	Object.assign(f, { radius:'', lat:'', lon:'', q:'', gender:'', plan:'', has_image:false, verified:false, age_min:'', age_max:'', area:'' })
	items.value = []; 
  hasNext.value=false; 
  page.value=1
}

async function buildMatchedSet(limitPages=5){
	const s = new Set()
	for(let p=1; 
  p<=limitPages; 
  p++){
		const d = await fetchMatches(p)
		const rows = Array.isArray(d) ? d : (d.results || [])
		rows.forEach(r => { const uid = r.partner?.id || r.user?.id; 
  if (uid) s.add(uid) })
		if(!d?.next) break
	}
	matchedSet.value = s
}

async function like(uid){
	try{
		const r = await likeUser(uid)
		if(r?.matched) router.push(`/chats/${uid}`)
		else alert('いいねを送りました')
	}catch{ alert('送信に失敗しました') }
}

onMounted(async () => {
	await buildMatchedSet()
	currentParams.value = toDetailParams()
	await load(currentParams.value, 1)
})
</script>

<template>
	<div class="wrap">
		<div class="d-flex align-items-center justify-content-between my-3">
			<div class="h2 fw-bold mb-0">検索</div>
			<!-- <button class="btn btn-outline-primary d-flex align-items-center gap-2" @click="showSidebar = true">
				<IconAdjustmentsHorizontal :size="18" /> 絞り込み
			</button> -->
		</div>

		<!-- サイドバー -->
		<SearchSidebar
			v-model="showSidebar"
			:f="f"
			@geo-search="onGeoSearch"
			@detail-search="onDetailSearch"
			@reset="onReset"
		/>

		<!-- 結果 -->
		<div v-if="loading" class="text-center py-5"><div class="spinner-border" role="status"></div></div>
		<div v-else-if="err" class="alert alert-danger">{{ err }}</div>

		<div v-else class="feed">
			<template v-if="items.length">
				<UserCard
					v-for="p in items"
					:key="p.user?.id"
					:user="p"
					:pfvs="[]"
					:matched="matchedSet.has(p.user?.id)"
					@message="$router.push('/chats/' + p.user?.id)"
					@like="like"
					@open="$router.push('/users/' + p.user?.id)"
				/>
				<div class="text-center mt-3" v-if="hasNext">
					<button class="btn btn-outline-primary" @click="more">もっと見る</button>
				</div>
			</template>
			<div v-else class="text-center text-muted py-5">条件に合うユーザーがいません</div>
		</div>

		<!-- モバイル用 FAB（任意） -->
		<button class="fab btn btn-light text-primary shadow" @click="showSidebar = true">
			<IconAdjustmentsHorizontal :size="20" />
		</button>
	</div>
</template>

<style scoped lang="scss">
.fab{
  position: fixed;
  right: 16px;
  bottom: 88px;
  border-radius: 999px;
  width: 56px;
  height: 56px;
  display:flex;
  align-items:center;
  justify-content:center;
  z-index: 1030;
  }
</style>
