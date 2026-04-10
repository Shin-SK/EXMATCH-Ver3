<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { fetchProfiles, fetchMatches, fetchLikesSent, likeUser } from '@/api'
import UserCard from '@/components/UserCard.vue'
import { IconMapPin, IconLoader2, IconAdjustmentsHorizontal, IconX, IconSearch } from '@tabler/icons-vue'
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
const totalCount = ref(0)
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

// ── 年齢 ──
const AGE_MIN = 18
const AGE_MAX = 60
const ageMin = ref(AGE_MIN)
const ageMax = ref(AGE_MAX)

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
	f.age_min = v === AGE_MIN ? '' : String(v)
}

function onAgeMaxInput(e) {
	let v = Number(e.target.value)
	if (v < ageMin.value) v = ageMin.value
	ageMax.value = v
	f.age_max = v === AGE_MAX ? '' : String(v)
}

// ── 性別 ──
const genderOptions = [
	{ label: '指定なし', value: '' },
	{ label: '男性', value: 'male' },
	{ label: '女性', value: 'female' },
]
const genderLabel = computed(() => genderOptions.find(g => g.value === f.gender)?.label || '')

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
}

function toggleFilter(key) {
	f[key] = !f[key]
}

// ── アクティブフィルターchip ──
const activeChips = computed(() => {
	const arr = []
	if (selectedDistance.value) arr.push({ key:'distance', label: distanceOptions.find(d=>d.value===selectedDistance.value)?.label })
	if (ageLabel.value !== '指定なし') arr.push({ key:'age', label: ageLabel.value })
	if (f.gender) arr.push({ key:'gender', label: genderLabel.value })
	if (selectedLciq.value !== '指定なし') arr.push({ key:'lciq', label: 'LCIQ ' + selectedLciq.value })
	if (f.has_plus) arr.push({ key:'has_plus', label: 'プラスプロフ' })
	if (f.has_image) arr.push({ key:'has_image', label: '写真あり' })
	if (f.verified) arr.push({ key:'verified', label: '本人確認済' })
	if (f.area) arr.push({ key:'area', label: f.area })
	if (f.q) arr.push({ key:'q', label: f.q })
	return arr
})

function removeChip(key) {
	switch (key) {
		case 'distance': selectedDistance.value=''; f.radius=''; break
		case 'age': ageMin.value=AGE_MIN; ageMax.value=AGE_MAX; f.age_min=''; f.age_max=''; break
		case 'gender': f.gender=''; break
		case 'lciq': selectedLciq.value='指定なし'; f.lciq_min=''; f.lciq_max=''; break
		case 'has_plus': f.has_plus=false; break
		case 'has_image': f.has_image=false; break
		case 'verified': f.verified=false; break
		case 'area': f.area=''; break
		case 'q': f.q=''; break
	}
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
		totalCount.value = d?.count ?? rows.length
		page.value = p
	} catch (e) {
		err.value = '読み込みに失敗しました'
		console.error('[Search]', e?.response?.status, e?.response?.data || e)
	} finally {
		loading.value = false
	}
}

const more = () => { if (hasNext.value) search(page.value + 1) }

// ── ボトムシート ──
const sheetOpen = ref(false)

function openSheet() {
	sheetOpen.value = true
	document.body.style.overflow = 'hidden'
}
function closeSheet() {
	sheetOpen.value = false
	document.body.style.overflow = ''
}
function applySheet() {
	closeSheet()
	search()
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
	ageMin.value = AGE_MIN
	ageMax.value = AGE_MAX
	located.value = false
}

async function buildMatchedSet(limitPages = 5) {
	const s = new Set()
	for (let p = 1; p <= limitPages; p++) {
		const d = await fetchMatches(p)
		const rows = Array.isArray(d) ? d : (d.results || [])
		rows.forEach(r => {
			const uid = r.partner?.id || r.user?.id
			if (uid) s.add(Number(uid))
		})
		if (!d?.next) break
	}
	matchedSet.value = s
}

const likedSet = ref(new Set())
const likingSet = ref(new Set())

async function like(uid) {
	const id = Number(uid)
	if (likingSet.value.has(id)) return
	likingSet.value = new Set([...likingSet.value, id])
	try {
		const r = await likeUser(id)
		if (r?.matched) {
			matchedSet.value = new Set([...matchedSet.value, id])
		} else {
			likedSet.value = new Set([...likedSet.value, id])
		}
	} catch (e) {
		console.error('[like]', id, e?.response?.status, e?.response?.data || e)
		alert('送信に失敗しました')
	} finally {
		const s = new Set(likingSet.value)
		s.delete(id)
		likingSet.value = s
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
				if (uid) s.add(Number(uid))
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
		<div class="head-set">
			<h2>SEARCH</h2>
			<h3>お相手を探す</h3>
		</div>
		<!-- ヘッダー -->
		<div class="search-header">
			<button class="filter-btn" @click="openSheet">
				<IconAdjustmentsHorizontal :size="18" />
				<span>絞り込み</span>
				<span v-if="activeChips.length" class="badge">{{ activeChips.length }}</span>
			</button>
		</div>

		<!-- アクティブフィルターchipバー -->
		<div v-if="activeChips.length" class="active-chips">
			<button
				v-for="c in activeChips" :key="c.key"
				class="active-chip"
				@click="removeChip(c.key)"
			>
				{{ c.label }}
				<IconX :size="12" />
			</button>
		</div>

		<!-- 結果カウント -->
		<div v-if="!loading || page > 1" class="result-count">
			{{ totalCount }}人がヒット
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
			<div v-else class="empty">
				<p>条件に合うユーザーがいません</p>
				<button class="btn-empty" @click="openSheet">条件を変更する</button>
			</div>
		</div>

		<!-- ボトムシート -->
		<transition name="sheet">
			<div v-if="sheetOpen" class="sheet-backdrop" @click.self="closeSheet">
				<div class="sheet">
					<div class="sheet-handle"></div>
					<div class="sheet-header">
						<h2>絞り込み条件</h2>
						<button class="close-btn" @click="closeSheet"><IconX :size="20" /></button>
					</div>

					<div class="sheet-body">
						<!-- 距離 -->
						<section class="sec">
							<div class="sec-label">
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
						</section>

						<!-- 年齢 -->
						<section class="sec">
							<div class="sec-label">
								年齢
								<span class="age-value">{{ ageLabel }}</span>
							</div>
							<div class="range-slider">
								<div class="range-track">
									<div class="range-fill" :style="ageTrackStyle"></div>
								</div>
								<input type="range" class="range-input" :min="AGE_MIN" :max="AGE_MAX" :value="ageMin" @input="onAgeMinInput" />
								<input type="range" class="range-input" :min="AGE_MIN" :max="AGE_MAX" :value="ageMax" @input="onAgeMaxInput" />
							</div>
						</section>

						<!-- 性別 -->
						<section class="sec">
							<div class="sec-label">性別</div>
							<div class="chips">
								<button
									v-for="g in genderOptions" :key="g.value"
									class="chip" :class="{ active: f.gender === g.value }"
									@click="f.gender = g.value"
								>{{ g.label }}</button>
							</div>
						</section>

						<!-- LCIQ -->
						<section class="sec">
							<div class="sec-label">LCIQスコア</div>
							<div class="chips">
								<button
									v-for="l in lciqOptions" :key="l.label"
									class="chip" :class="{ active: selectedLciq === l.label }"
									@click="selectLciq(l)"
								>{{ l.label }}</button>
							</div>
						</section>

						<!-- トグル -->
						<section class="sec">
							<div class="sec-label">こだわり</div>
							<div class="chips">
								<button class="chip" :class="{ active: f.has_plus }" @click="toggleFilter('has_plus')">プラスプロフィール</button>
								<button class="chip" :class="{ active: f.has_image }" @click="toggleFilter('has_image')">写真あり</button>
								<button class="chip" :class="{ active: f.verified }" @click="toggleFilter('verified')">本人確認済み</button>
							</div>
						</section>

						<!-- エリア・キーワード -->
						<section class="sec">
							<div class="sec-label">エリア</div>
							<input v-model="f.area" class="field-input" placeholder="渋谷、大阪など">
						</section>

						<section class="sec">
							<div class="sec-label">キーワード</div>
							<div class="field-with-icon">
								<IconSearch :size="16" class="field-icon" />
								<input v-model="f.q" class="field-input has-icon" placeholder="ニックネーム / 自己紹介">
							</div>
						</section>
					</div>

					<div class="sheet-footer">
						<button class="btn-reset" @click="resetAll">リセット</button>
						<button class="btn-apply" @click="applySheet">この条件で検索</button>
					</div>
				</div>
			</div>
		</transition>
	</div>
</template>

<style scoped lang="scss">
$mc: #004C71;

.search-page {
	padding-top: 8px;
}

/* ── ヘッダー ── */
.search-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin: 12px 0;
}
.page-title {
	font-size: 1.4rem;
	font-weight: 700;
	margin: 0;
}
.filter-btn {
	display: flex;
	align-items: center;
	gap: 6px;
	padding: 8px 14px;
	border: 1px solid #e2e6ea;
	background: #fff;
	border-radius: 100px;
	font-size: 0.8rem;
	font-weight: 600;
	color: #333;
	cursor: pointer;
	transition: all .2s;
	&:hover { border-color: $mc; color: $mc; }
	.badge {
		background: $mc;
		color: #fff;
		font-size: 0.65rem;
		font-weight: 700;
		min-width: 18px;
		height: 18px;
		padding: 0 5px;
		border-radius: 100px;
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
}

/* ── アクティブchip ── */
.active-chips {
	display: flex;
	gap: 6px;
	overflow-x: auto;
	padding-bottom: 8px;
	margin-bottom: 4px;
	-webkit-overflow-scrolling: touch;
	scrollbar-width: none;
	&::-webkit-scrollbar { display: none; }
}
.active-chip {
	display: inline-flex;
	align-items: center;
	gap: 4px;
	padding: 5px 10px 5px 12px;
	border-radius: 100px;
	border: none;
	background: $mc;
	color: #fff;
	font-size: 0.72rem;
	font-weight: 600;
	white-space: nowrap;
	cursor: pointer;
	flex-shrink: 0;
}

.result-count {
	font-size: 0.75rem;
	color: #888;
	margin-bottom: 10px;
	padding-left: 2px;
}

.empty {
	text-align: center;
	padding: 60px 20px;
	color: #888;
	.btn-empty {
		margin-top: 12px;
		padding: 8px 20px;
		border: 1px solid $mc;
		background: #fff;
		color: $mc;
		border-radius: 100px;
		font-size: 0.8rem;
		font-weight: 600;
		cursor: pointer;
	}
}

/* ── ボトムシート ── */
.sheet-backdrop {
	position: fixed;
	inset: 0;
	background: rgba(0,0,0,.45);
	z-index: 1050;
	display: flex;
	align-items: flex-end;
	justify-content: center;
}
.sheet {
	background: #fff;
	width: 100%;
	max-width: 560px;
	max-height: 90vh;
	border-radius: 20px 20px 0 0;
	display: flex;
	flex-direction: column;
	box-shadow: 0 -8px 30px rgba(0,0,0,.15);
}
.sheet-handle {
	width: 40px;
	height: 4px;
	background: #d8dde2;
	border-radius: 2px;
	margin: 10px auto 0;
}
.sheet-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 14px 18px 10px;
	h2 { font-size: 1rem; font-weight: 700; margin: 0; }
	.close-btn {
		border: none;
		background: none;
		color: #888;
		cursor: pointer;
		padding: 4px;
		display: flex;
		&:hover { color: #333; }
	}
}
.sheet-body {
	padding: 8px 18px 18px;
	overflow-y: auto;
	flex: 1;
}
.sec {
	padding: 14px 0;
	border-bottom: 1px solid #f2f4f6;
	&:last-child { border-bottom: none; }
}
.sec-label {
	display: flex;
	align-items: center;
	gap: 4px;
	font-size: 0.8rem;
	font-weight: 600;
	color: #555;
	margin-bottom: 10px;
	.locating {
		font-weight: 400;
		color: #999;
		font-size: 0.72rem;
		display: flex;
		align-items: center;
		gap: 2px;
		margin-left: 4px;
	}
}

.sheet-footer {
	display: flex;
	gap: 10px;
	padding: 12px 18px calc(12px + env(safe-area-inset-bottom));
	border-top: 1px solid #f0f2f4;
	background: #fff;
}
.btn-reset {
	flex: 0 0 auto;
	padding: 12px 22px;
	border: 1px solid #e2e6ea;
	border-radius: 100px;
	background: #fff;
	color: #666;
	font-size: 0.85rem;
	font-weight: 600;
	cursor: pointer;
	&:hover { background: #f5f7f9; }
}
.btn-apply {
	flex: 1;
	padding: 12px;
	border: none;
	border-radius: 100px;
	background: $mc;
	color: #fff;
	font-size: 0.9rem;
	font-weight: 700;
	cursor: pointer;
	&:hover { opacity: .9; }
}

/* ── chip共通 ── */
.chips { display: flex; gap: 6px; flex-wrap: wrap; }
.chip {
	padding: 8px 16px;
	border-radius: 100px;
	border: 1px solid #e8ecf0;
	background: #fff;
	font-size: 0.8rem;
	color: #333;
	cursor: pointer;
	transition: all .15s;
	white-space: nowrap;
	&:hover { background: #f5f7f9; }
	&.active {
		background: $mc;
		color: #fff;
		border-color: $mc;
	}
}

/* ── 年齢スライダー ── */
.age-value {
	font-weight: 600;
	color: $mc;
	margin-left: auto;
	font-size: 0.85rem;
}
.range-slider {
	position: relative;
	height: 32px;
	padding-top: 8px;
}
.range-track {
	position: absolute;
	top: 14px;
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
	top: 4px;
	left: 0;
	width: 100%;
	-webkit-appearance: none;
	appearance: none;
	background: transparent;
	pointer-events: none;
	margin: 0;
	height: 24px;
	&::-webkit-slider-runnable-track { height: 4px; background: transparent; }
	&::-webkit-slider-thumb {
		-webkit-appearance: none;
		width: 22px; height: 22px;
		border-radius: 50%;
		background: #fff;
		border: 2px solid $mc;
		margin-top: -9px;
		pointer-events: auto;
		cursor: pointer;
		box-shadow: 0 1px 3px rgba(0,0,0,.15);
	}
	&::-moz-range-track { height: 4px; background: transparent; border: none; }
	&::-moz-range-thumb {
		width: 22px; height: 22px;
		border-radius: 50%;
		background: #fff;
		border: 2px solid $mc;
		pointer-events: auto;
		cursor: pointer;
		box-shadow: 0 1px 3px rgba(0,0,0,.15);
	}
}

/* ── 入力 ── */
.field-input {
	width: 100%;
	padding: 11px 14px;
	border-radius: 10px;
	border: 1px solid #e8ecf0;
	background: #fff;
	font-size: 0.85rem;
	color: #333;
	&:focus { outline: none; border-color: $mc; }
}
.field-with-icon {
	position: relative;
	.field-icon {
		position: absolute;
		left: 12px;
		top: 50%;
		transform: translateY(-50%);
		color: #aaa;
	}
	.field-input.has-icon { padding-left: 36px; }
}

.spin { animation: spin 1s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

/* ── トランジション ── */
.sheet-enter-active, .sheet-leave-active {
	transition: opacity .25s ease;
	.sheet { transition: transform .3s cubic-bezier(.2,.8,.2,1); }
}
.sheet-enter-from, .sheet-leave-to {
	opacity: 0;
	.sheet { transform: translateY(100%); }
}
</style>
