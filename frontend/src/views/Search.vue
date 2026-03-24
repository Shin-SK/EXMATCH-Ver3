<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { fetchProfiles, fetchMatches, fetchLikesSent, likeUser } from '@/api'
import UserCard from '@/components/UserCard.vue'
import { IconMapPin, IconChevronDown, IconLoader2 } from '@tabler/icons-vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const f = reactive({
	radius:'', lat:'', lon:'',
	q:'', gender:'', plan:'',
	has_image:false, verified:false, has_plus:false,
	age_min:'', age_max:'', area:'',
	lciq_min:'', lciq_max:'',
})

const loading = ref(true)
const err = ref('')
const items = ref([])
const page = ref(1)
const hasNext = ref(false)
const matchedSet = ref(new Set())

// ── 距離 ──
const distanceOptions = [
	{ label: '指定なし', value: '' },
	{ label: '5km', value: '5' },
	{ label: '10km', value: '10' },
	{ label: '30km', value: '30' },
	{ label: '50km+', value: '50' },
]
const selectedDistance = ref('')
const locating = ref(false)
const located = ref(false)

function selectDistance(val) {
	selectedDistance.value = val
	f.radius = val
	if (val && !located.value) locate()
	else search()
}

function locate() {
	if (!navigator.geolocation) { alert('位置情報が利用できません'); return }
	locating.value = true
	navigator.geolocation.getCurrentPosition(
		pos => {
			f.lat = String(pos.coords.latitude)
			f.lon = String(pos.coords.longitude)
			located.value = true
			locating.value = false
			search()
		},
		() => {
			alert('位置情報の取得に失敗しました')
			locating.value = false
			selectedDistance.value = ''
			f.radius = ''
		},
		{ enableHighAccuracy: false, timeout: 6000 }
	)
}

// ── 年齢（デュアルレンジスライダー）──
const AGE_MIN = 18
const AGE_MAX = 60
const ageMin = ref(AGE_MIN)
const ageMax = ref(AGE_MAX)
let ageTimer = null

const ageLabel = computed(() => {
	if (ageMin.value === AGE_MIN && ageMax.value === AGE_MAX) return '指定なし'
	if (ageMax.value === AGE_MAX) return `${ageMin.value}歳〜`
	if (ageMin.value === AGE_MIN) return `〜${ageMax.value}歳`
	return `${ageMin.value}〜${ageMax.value}歳`
})

const ageTrackStyle = computed(() => {
	const lo = ((ageMin.value - AGE_MIN) / (AGE_MAX - AGE_MIN)) * 100
	const hi = ((ageMax.value - AGE_MIN) / (AGE_MAX - AGE_MIN)) * 100
	return { left: lo + '%', width: (hi - lo) + '%' }
})

function onAgeMinInput(e) {
	let v = Number(e.target.value)
	if (v > ageMax.value) v = ageMax.value
	ageMin.value = v
	debouncedAgeSearch()
}

function onAgeMaxInput(e) {
	let v = Number(e.target.value)
	if (v < ageMin.value) v = ageMin.value
	ageMax.value = v
	debouncedAgeSearch()
}

function debouncedAgeSearch() {
	f.age_min = ageMin.value === AGE_MIN ? '' : String(ageMin.value)
	f.age_max = ageMax.value === AGE_MAX ? '' : String(ageMax.value)
	clearTimeout(ageTimer)
	ageTimer = setTimeout(() => search(), 300)
}

// ── 性別 ──
const genderOptions = [
	{ label: '指定なし', value: '' },
	{ label: '男性', value: 'male' },
	{ label: '女性', value: 'female' },
]

function selectGender(val) {
	f.gender = val
	search()
}

// ── その他（折りたたみ）──
const showMore = ref(false)

// LCIQ
const lciqOptions = [
	{ label: '指定なし', min: '', max: '' },
	{ label: '〜50点',   min: '',   max: '50' },
	{ label: '51〜70点', min: '51', max: '70' },
	{ label: '71〜90点', min: '71', max: '90' },
	{ label: '91〜100点', min: '91', max: '100' },
]
const selectedLciq = ref('指定なし')

function selectLciq(opt) {
	selectedLciq.value = opt.label
	f.lciq_min = opt.min
	f.lciq_max = opt.max
	search()
}

function toggleFilter(key) {
	f[key] = !f[key]
	search()
}

// ── 検索 ──
function buildParams() {
	const p = {}
	if (f.radius && f.lat && f.lon) { p.radius = f.radius; p.lat = f.lat; p.lon = f.lon }
	if (f.q) p.q = f.q
	if (f.gender) p.gender = f.gender
	if (f.has_image) p.has_image = '1'
	if (f.verified) p.verified = '1'
	if (f.has_plus) p.has_plus = '1'
	if (f.age_min) p.age_min = f.age_min
	if (f.age_max) p.age_max = f.age_max
	if (f.area) p.area = f.area
	if (f.lciq_min) p.lciq_min = f.lciq_min
	if (f.lciq_max) p.lciq_max = f.lciq_max
	return p
}

const currentParams = ref({})

async function search(p = 1) {
	loading.value = true
	err.value = ''
	currentParams.value = buildParams()
	try {
		const d = await fetchProfiles(currentParams.value, p)
		const rows = Array.isArray(d) ? d : (d.results || d.items || [])
		items.value = p === 1 ? rows : [...items.value, ...rows]
		hasNext.value = !!d?.next
		page.value = p
	} catch (e) {
		err.value = '読み込みに失敗しました'
		console.error('[Search]', e?.response?.status, e?.response?.data || e)
	} finally {
		loading.value = false
	}
}

const more = () => { if (hasNext.value) search(page.value + 1) }

// アクティブフィルター数（折りたたみ内）
function moreFilterCount() {
	let n = 0
	if (selectedLciq.value !== '指定なし') n++
	if (f.has_plus) n++
	if (f.has_image) n++
	if (f.verified) n++
	if (f.area) n++
	if (f.q) n++
	return n
}

function resetAll() {
	Object.assign(f, {
		radius:'', lat:'', lon:'', q:'', gender:'', plan:'',
		has_image:false, verified:false, has_plus:false,
		age_min:'', age_max:'', area:'',
		lciq_min:'', lciq_max:'',
	})
	selectedDistance.value = ''
	selectedLciq.value = '指定なし'
	located.value = false
	search()
}

async function buildMatchedSet(limitPages = 5) {
	const s = new Set()
	for (let p = 1; p <= limitPages; p++) {
		const d = await fetchMatches(p)
		const rows = Array.isArray(d) ? d : (d.results || [])
		rows.forEach(r => {
			const uid = r.partner?.id || r.user?.id
			if (uid) s.add(uid)
		})
		if (!d?.next) break
	}
	matchedSet.value = s
}

const likedSet = ref(new Set())

async function like(uid) {
	try {
		const r = await likeUser(uid)
		if (r?.matched) {
			matchedSet.value = new Set([...matchedSet.value, uid])
		} else {
			likedSet.value = new Set([...likedSet.value, uid])
		}
	} catch (e) {
		console.error('[like]', uid, e?.response?.status, e?.response?.data || e)
		alert('送信に失敗しました')
	}
}

async function buildLikedSet(limitPages = 5) {
	try {
		const s = new Set()
		for (let p = 1; p <= limitPages; p++) {
			const d = await fetchLikesSent(p)
			const rows = Array.isArray(d) ? d : (d.results || [])
			rows.forEach(r => {
				const uid = r.to_user?.id || r.user?.id
				if (uid) s.add(uid)
			})
			if (!d?.next) break
		}
		likedSet.value = s
	} catch (e) {
		console.warn('[buildLikedSet]', e)
	}
}

onMounted(async () => {
	await Promise.all([
		buildMatchedSet().catch(e => console.warn('[buildMatchedSet]', e)),
		buildLikedSet(),
	])
	await search()
})
</script>

<template>
	<div class="search-page">
		<h1 class="h2 fw-bold my-3">検索</h1>

		<div class="search-bar">
			<!-- 距離 -->
			<div class="search-section">
				<div class="section-label">
					<IconMapPin :size="15" />
					距離
					<span v-if="locating" class="locating"><IconLoader2 :size="13" class="spin" /> 取得中…</span>
				</div>
				<div class="chips">
					<button
						v-for="d in distanceOptions" :key="d.value"
						class="chip" :class="{ active: selectedDistance === d.value }"
						@click="selectDistance(d.value)"
					>{{ d.label }}</button>
				</div>
			</div>

			<!-- 年齢（デュアルレンジスライダー） -->
			<div class="search-section">
				<div class="section-label">
					年齢
					<span class="age-value">{{ ageLabel }}</span>
				</div>
				<div class="range-slider">
					<div class="range-track">
						<div class="range-fill" :style="ageTrackStyle"></div>
					</div>
					<input
						type="range"
						class="range-input"
						:min="AGE_MIN" :max="AGE_MAX"
						:value="ageMin"
						@input="onAgeMinInput"
					/>
					<input
						type="range"
						class="range-input"
						:min="AGE_MIN" :max="AGE_MAX"
						:value="ageMax"
						@input="onAgeMaxInput"
					/>
					<div class="range-labels">
						<span>{{ AGE_MIN }}</span>
						<span>{{ AGE_MAX }}</span>
					</div>
				</div>
			</div>

			<!-- 性別 -->
			<div class="search-section mt-2">
				<div class="section-label">性別</div>
				<div class="chips">
					<button
						v-for="g in genderOptions" :key="g.value"
						class="chip" :class="{ active: f.gender === g.value }"
						@click="selectGender(g.value)"
					>{{ g.label }}</button>
				</div>
			</div>

			<!-- その他（折りたたみ） -->
			<button class="more-toggle" @click="showMore = !showMore">
				その他の条件
				<span class="more-count" v-if="moreFilterCount()">{{ moreFilterCount() }}</span>
				<IconChevronDown :size="14" :style="{ transform: showMore ? 'rotate(180deg)' : '', transition: 'transform .2s' }" />
			</button>

			<div class="more-filters" v-show="showMore">
				<!-- LCIQ -->
				<div class="more-section">
					<div class="more-label">LCIQスコア</div>
					<div class="chips">
						<button
							v-for="l in lciqOptions" :key="l.label"
							class="chip" :class="{ active: selectedLciq === l.label }"
							@click="selectLciq(l)"
						>{{ l.label }}</button>
					</div>
				</div>

				<!-- トグル -->
				<div class="more-section">
					<div class="chips">
						<button class="chip" :class="{ active: f.has_plus }" @click="toggleFilter('has_plus')">プラスプロフィール</button>
						<button class="chip" :class="{ active: f.has_image }" @click="toggleFilter('has_image')">写真あり</button>
						<button class="chip" :class="{ active: f.verified }" @click="toggleFilter('verified')">本人確認済み</button>
					</div>
				</div>

				<!-- エリア・キーワード -->
				<div class="more-section">
					<div class="text-fields">
						<div class="text-field">
							<label>エリア</label>
							<input v-model="f.area" class="field-input" placeholder="渋谷、大阪など" @keyup.enter="search()">
						</div>
						<div class="text-field">
							<label>キーワード</label>
							<input v-model="f.q" class="field-input" placeholder="ニックネーム/自己紹介" @keyup.enter="search()">
						</div>
					</div>
				</div>

				<div class="more-actions">
					<button class="btn-reset" @click="resetAll">条件をリセット</button>
				</div>
			</div>
		</div>

		<!-- 結果 -->
		<div v-if="loading && page === 1" class="text-center py-5"><div class="spinner-border" role="status"></div></div>
		<div v-else-if="err" class="alert alert-danger">{{ err }}</div>

		<div v-else class="feed">
			<template v-if="items.length">
				<UserCard
					v-for="p in items"
					:key="p.id"
					:user="p"
					:pfvs="[]"
					:matched="matchedSet.has(p.id)"
					:liked="likedSet.has(p.id)"
					@message="$router.push('/chats/' + p.id)"
					@like="like"
					@open="$router.push('/users/' + p.id)"
				/>
				<div class="text-center mt-3" v-if="hasNext">
					<button class="btn btn-outline-primary" @click="more">もっと見る</button>
				</div>
			</template>
			<div v-else class="text-center text-muted py-5">条件に合うユーザーがいません</div>
		</div>
	</div>
</template>

<style scoped lang="scss">
$mc: #004C71;

.search-page {
	padding-top: 8px;
}

.search-bar {
	background: #fff;
	border-radius: 12px;
	padding: 16px;
	margin-bottom: 16px;
}

.search-section {
	margin-bottom: 14px;
}

.section-label {
	display: flex;
	align-items: center;
	gap: 4px;
	font-size: 0.8rem;
	font-weight: 600;
	color: #555;
	margin-bottom: 8px;
	.locating {
		font-weight: 400;
		color: #999;
		font-size: 0.75rem;
		display: flex;
		align-items: center;
		gap: 2px;
		margin-left: 4px;
	}
}

/* ── 共通ピル ── */
.chips {
	display: flex;
	gap: 6px;
	flex-wrap: wrap;
}

.chip {
	padding: 6px 14px;
	border-radius: 100px;
	border: none;
	background: #f5f7f9;
	font-size: 0.8rem;
	color: #333;
	cursor: pointer;
	transition: background .2s, color .2s;
	white-space: nowrap;
	&:hover { background: #e8ecf0; }
	&.active {
		background: $mc;
		color: #fff;
	}
}

/* ── 年齢スライダー ── */
.age-value {
	font-weight: 400;
	color: $mc;
	margin-left: auto;
	font-size: 0.8rem;
}

.range-slider {
	position: relative;
	height: 40px;
	padding-top: 8px;
}

.range-track {
	position: absolute;
	top: 16px;
	left: 0;
	right: 0;
	height: 4px;
	background: #e8ecf0;
	border-radius: 2px;
}

.range-fill {
	position: absolute;
	height: 100%;
	background: $mc;
	border-radius: 2px;
}

.range-input {
	position: absolute;
	top: 6px;
	left: 0;
	width: 100%;
	-webkit-appearance: none;
	appearance: none;
	background: transparent;
	pointer-events: none;
	margin: 0;
	height: 24px;

	&::-webkit-slider-runnable-track {
		height: 4px;
		background: transparent;
	}
	&::-webkit-slider-thumb {
		-webkit-appearance: none;
		width: 22px;
		height: 22px;
		border-radius: 50%;
		background: #fff;
		border: 2px solid $mc;
		margin-top: -9px;
		pointer-events: auto;
		cursor: pointer;
		box-shadow: 0 1px 3px rgba(0,0,0,.15);
	}
	&::-moz-range-track {
		height: 4px;
		background: transparent;
		border: none;
	}
	&::-moz-range-thumb {
		width: 22px;
		height: 22px;
		border-radius: 50%;
		background: #fff;
		border: 2px solid $mc;
		pointer-events: auto;
		cursor: pointer;
		box-shadow: 0 1px 3px rgba(0,0,0,.15);
	}
}

.range-labels {
	display: flex;
	justify-content: space-between;
	margin-top: 24px;
	font-size: 0.65rem;
	color: #bbb;
}

/* ── その他トグル ── */
.more-toggle {
	display: flex;
	align-items: center;
	gap: 6px;
	border: none;
	background: none;
	font-size: 0.8rem;
	font-weight: 600;
	color: #888;
	cursor: pointer;
	padding: 0;
	&:hover { color: $mc; }
}

.more-count {
	background: $mc;
	color: #fff;
	font-size: 0.65rem;
	font-weight: 700;
	width: 18px;
	height: 18px;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
}

.more-filters {
	margin-top: 14px;
	padding-top: 14px;
	border-top: 1px solid #f0f0f0;
}

.more-section {
	margin-bottom: 12px;
	&:last-of-type { margin-bottom: 0; }
}

.more-label {
	font-size: 0.75rem;
	font-weight: 600;
	color: #888;
	margin-bottom: 6px;
}

/* ── テキスト入力 ── */
.text-fields {
	display: flex;
	gap: 8px;
	flex-wrap: wrap;
}

.text-field {
	flex: 1;
	min-width: 140px;
	label {
		display: block;
		font-size: 0.75rem;
		font-weight: 600;
		color: #888;
		margin-bottom: 4px;
	}
}

.field-input {
	width: 100%;
	padding: 8px 10px;
	border-radius: 8px;
	border: none;
	background: #f5f7f9;
	font-size: 0.8rem;
	color: #333;
	&:focus { outline: none; background: #e8ecf0; }
}

.more-actions {
	margin-top: 12px;
	text-align: center;
}

.btn-reset {
	padding: 6px 20px;
	border: none;
	border-radius: 100px;
	background: #f5f7f9;
	color: #666;
	font-size: 0.8rem;
	cursor: pointer;
	&:hover { background: #e8ecf0; }
}

.spin {
	animation: spin 1s linear infinite;
}
@keyframes spin {
	from { transform: rotate(0deg); }
	to { transform: rotate(360deg); }
}
</style>
