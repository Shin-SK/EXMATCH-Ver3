<script setup>
import { computed } from 'vue'
import { IconLocation, IconSearch, IconX } from '@tabler/icons-vue'

const props = defineProps({
	modelValue: { type: Boolean, default: false },
	f: { type: Object, required: true },
})
const emit = defineEmits(['update:modelValue','geo-search','detail-search','reset'])

const isOpen = computed({
	get: () => props.modelValue,
	set: v  => emit('update:modelValue', v)
})

function close(){ isOpen.value = false }
function onGeo(){ emit('geo-search'); close() }
function onDetail(){ emit('detail-search'); close() }
function onReset(){ emit('reset') }

function locate(){
	if(!navigator.geolocation){ alert('位置情報が利用できません'); return }
	navigator.geolocation.getCurrentPosition(
		pos => {
			props.f.lat = String(pos.coords.latitude)
			props.f.lon = String(pos.coords.longitude)
		},
		err => { console.warn(err); alert('位置情報の取得に失敗しました') },
		{ enableHighAccuracy:false, timeout:6000 }
	)
}
</script>

<template>
	<div v-show="isOpen" class="sb">
		<div class="sb__overlay" @click="close" />
		<aside class="sb__panel">
			<div class="sb__head">
				<strong>検索条件</strong>
				<button class="btn btn-sm btn-outline-secondary" @click="close" aria-label="閉じる">
					<IconX :size="18" />
				</button>
			</div>

			<div class="sb__body">
				<!-- 現在地検索 -->
				<div class="item radius mb-3">
					<h2 class="h6 d-flex align-items-center gap-1">
						<IconLocation :size="16" /> 現在地からの距離（km）
					</h2>

					<div class="d-flex flex-column align-items-start gap-2 mt-2 w-100">
						<button class="btn btn-outline-secondary btn-sm" type="button" @click="locate">現在地を取得</button>
						<span class="text-muted small">lat: {{ f.lat || '-' }}, lon: {{ f.lon || '-' }}</span>
					</div>

					<input class="form-control my-3" v-model="f.radius" placeholder="例: 5（数字のみ）" inputmode="numeric">
					<div class="d-grid gap-2">
						<button type="button" class="btn btn-primary" @click="onGeo">距離で検索</button>
					</div>
				</div>

				<!-- 詳細検索 -->
				<h2 class="h6 d-flex align-items-center gap-1 mt-3">
					<IconSearch :size="16" /> プロフィール検索
				</h2>

				<div class="detail mt-2">
					<div class="mb-2">
						<label class="form-label">キーワード</label>
						<input class="form-control" v-model="f.q" placeholder="ニックネーム/自己紹介/エリア">
					</div>

					<div class="row g-2">
						<div class="col-6">
							<label class="form-label">性別</label>
							<select class="form-select" v-model="f.gender">
								<option value="">指定なし</option>
								<option value="male">男性</option>
								<option value="female">女性</option>
							</select>
						</div>
						<div class="col-6">
							<label class="form-label">プラン</label>
							<select class="form-select" v-model="f.plan">
								<option value="">指定なし</option>
								<option value="free">フリー</option>
								<option value="standard">スタンダード</option>
							</select>
						</div>
						<div class="col-6">
							<label class="form-label">年齢(下限)</label>
							<input class="form-control" v-model="f.age_min" inputmode="numeric" placeholder="18">
						</div>
						<div class="col-6">
							<label class="form-label">年齢(上限)</label>
							<input class="form-control" v-model="f.age_max" inputmode="numeric" placeholder="40">
						</div>
					</div>

					<div class="mt-2">
						<label class="form-label">エリア</label>
						<input class="form-control" v-model="f.area" placeholder="渋谷など">
					</div>

					<div class="d-flex gap-3 align-items-center mt-2">
						<div class="form-check">
							<input class="form-check-input" type="checkbox" id="hasImg" v-model="f.has_image">
							<label class="form-check-label" for="hasImg">画像あり</label>
						</div>
						<div class="form-check">
							<input class="form-check-input" type="checkbox" id="verified" v-model="f.verified">
							<label class="form-check-label" for="verified">本人確認済</label>
						</div>
					</div>

					<div class="d-grid gap-2 my-3">
						<button type="button" class="btn btn-primary" @click="onDetail">条件で検索</button>
						<button type="button" class="btn btn-link btn-sm text-dark" @click="onReset">リセット</button>
					</div>
				</div>
			</div>
		</aside>
	</div>
</template>

<style scoped>
.sb{ position:fixed; inset:0; z-index:1050; }
.sb__overlay{ position:absolute; inset:0; background:rgba(0,0,0,.25); }
.sb__panel{ position:absolute; top:0; right:0; height:100%; width:min(92vw, 360px); background:#fff; box-shadow:-8px 0 24px rgba(0,0,0,.08); display:flex; flex-direction:column; }
.sb__head{ display:flex; justify-content:space-between; align-items:center; padding:12px 16px; border-bottom:1px solid #eee; }
.sb__body{ padding:12px 16px; overflow:auto; }
</style>
