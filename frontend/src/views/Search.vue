<!-- src/views/Search.vue（全文置換） -->
<script setup>
import { ref, reactive, onMounted } from 'vue'
import { fetchProfiles, fetchMatches, likeUser } from '@/api'
import UserCard from '@/components/UserCard.vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const f = reactive({
  // 現在地検索
  radius: '',  // km
  lat:    '',
  lon:    '',
  // 詳細検索
  q: '', gender: '', plan: '',
  has_image: false, verified: false,
  age_min: '', age_max: '', area: '',
})

const loading = ref(true)
const err = ref('')
const items = ref([])
const page = ref(1)
const hasNext = ref(false)
const matchedSet = ref(new Set())

function toGeoParams(){
  return {
    radius: f.radius || undefined,
    lat:    f.lat    || undefined,
    lon:    f.lon    || undefined,
  }
}
function toDetailParams(){
  return {
    q: f.q || undefined,
    gender:  f.gender  || undefined,
    plan:    f.plan    || undefined,
    has_image: f.has_image ? '1' : undefined,
    verified:  f.verified  ? '1' : undefined,
    age_min: f.age_min || undefined,
    age_max: f.age_max || undefined,
    area:    f.area    || undefined,
  }
}

async function load(params, p=1){
  loading.value = true; err.value=''
  try{
    const d = await fetchProfiles(params, p)
    const rows = Array.isArray(d) ? d : (d.results || d.items || [])
    items.value = p === 1 ? rows : [...items.value, ...rows]
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
async function onGeoSearch(){
  currentParams.value = toGeoParams()
  await load(currentParams.value, 1)
}
async function onDetailSearch(){
  currentParams.value = toDetailParams()
  await load(currentParams.value, 1)
}
function onReset(){
  Object.assign(f, {
    radius:'', lat:'', lon:'',
    q:'', gender:'', plan:'', has_image:false, verified:false,
    age_min:'', age_max:'', area:''
  })
  items.value = []; hasNext.value=false; page.value=1
}

async function buildMatchedSet(limitPages=5){
  const s = new Set()
  for(let p=1; p<=limitPages; p++){
    const d = await fetchMatches(p)
    const rows = Array.isArray(d) ? d : (d.results || [])
    rows.forEach(r => {
      const uid = r.partner?.id || r.user?.id
      if (uid) s.add(uid)
    })
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

function locate(){
  if(!navigator.geolocation) return alert('位置情報が利用できません')
  navigator.geolocation.getCurrentPosition(
    pos => { f.lat = String(pos.coords.latitude); f.lon = String(pos.coords.longitude) },
    err => { console.warn(err); alert('位置情報の取得に失敗しました') },
    { enableHighAccuracy:false, timeout:6000 }
  )
}

onMounted(async () => {
  await buildMatchedSet()
  // 初期は詳細空条件で一覧
  currentParams.value = toDetailParams()
  await load(currentParams.value, 1)
})
</script>

<template>
  <div class="wrap">
    <div class="h2 fw-bold my-3">検索</div>

    <div class="form__wrap">
      <!-- 現在地から検索（専用ボタン） -->
      <div class="filter">
        <div class="filter__wrap">
          <div class="item radius mb-2">
            <h2>
                <IconLocation :size="16" />
                現在地からの距離（km）
            </h2>

            <div class="d-flex flex-column align-items-center gap-2 mt-5 w-100">
              <button class="btn btn-outline-secondary" type="button" @click="locate">現在地を取得</button>
              <span class="text-muted small">lat: {{ f.lat || '-' }}, lon: {{ f.lon || '-' }}</span>
              <!-- ★ここ、未取得or取得済みのふたつで出し方変える感じでいいと思った。わざわざ数字出さなくてもと -->
            </div>

            <input class="form-control my-5" v-model="f.radius" placeholder="例: 5（数字のみ入力）" inputmode="numeric">

            <div class="button-area my-2 d-flex gap-2 flex-column">
              <button type="button" class="btn btn-primary w-100" @click="onGeoSearch">検索</button>
              <button type="button" class="btn btn-link text-dark btn-sm" @click="onReset">リセット</button>
            </div>
          </div>
        </div>

        <!-- 詳細検索（専用ボタン） -->
        <h2 class="d-flex align-items-center gap-1 mt-3">
          <IconSearch :size="16" />プロフィール検索
        </h2>

        <div class="filter__wrap detail mt-2">
          <div class="row g-4">
            <div class="col-12 col-md-4">
              <label class="form-label">キーワード</label>
              <input class="form-control field" v-model="f.q" placeholder="ニックネーム/自己紹介/エリア">
            </div>
            <div class="col-6 col-md-2">
              <label class="form-label">性別</label>
              <select class="form-select field" v-model="f.gender">
                <option value="">指定なし</option>
                <option value="male">男性</option>
                <option value="female">女性</option>
              </select>
            </div>
            <div class="col-6 col-md-2">
              <label class="form-label">プラン</label>
              <select class="form-select field" v-model="f.plan">
                <option value="">指定なし</option>
                <option value="free">フリー</option>
                <option value="standard">スタンダード</option>
              </select>
            </div>
            <div class="col-6 col-md-2">
              <label class="form-label">年齢(下限)</label>
              <input class="form-control field" v-model="f.age_min" inputmode="numeric" placeholder="18">
            </div>
            <div class="col-6 col-md-2">
              <label class="form-label">年齢(上限)</label>
              <input class="form-control field" v-model="f.age_max" inputmode="numeric" placeholder="40">
            </div>
            <div class="col-12 col-md-3">
              <label class="form-label">エリア</label>
              <input class="form-control field" v-model="f.area" placeholder="渋谷など">
            </div>
            <div class="col-12 col-md-3 d-flex align-items-end gap-3">
              <div class="form-check">
                <input class="form-check-input" type="checkbox" id="hasImg" v-model="f.has_image">
                <label class="form-check-label" for="hasImg">画像あり</label>
              </div>
              <div class="form-check">
                <input class="form-check-input" type="checkbox" id="verified" v-model="f.verified">
                <label class="form-check-label" for="verified">本人確認済</label>
              </div>
            </div>
          </div>

          <div class="button-area my-5 d-flex flex-column gap-2 ">
            <button type="button" class="btn btn-primary w-100" @click="onDetailSearch">検索</button>
            <button type="button" class="btn btn-link btn-sm text-dark" @click="onReset">リセット</button>
          </div>
        </div>
      </div>
    </div>

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
  </div>
</template>
