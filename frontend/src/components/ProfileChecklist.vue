<!-- src/components/ProfileChecklist.vue（Bootstrap非依存・SCSSに合わせた構造） -->
<script setup>
import { ref, computed, onMounted } from 'vue'
import { fetchMe, fetchProfileFields, fetchMyCustomFields } from '@/api'

const loading = ref(true)
const me = ref(null)
const fields = ref([])
const customVals = ref({})

const REQUIRED_FIXED = ['nickname','gender','main_area','sexual_object_pref','lciq_score','date_of_birth']

async function loadAll(){
  loading.value = true
  try{
    const [m, defs, vals] = await Promise.all([fetchMe(), fetchProfileFields(), fetchMyCustomFields()])
    me.value = m
    fields.value = Array.isArray(defs?.items) ? defs.items : (defs?.results || [])
    customVals.value = vals?.values || {}
  } finally { loading.value = false }
}
onMounted(loadAll)

// 不足カウント
const missingFixedCnt = computed(() => {
  if (!me.value) return 0
  return REQUIRED_FIXED.reduce((n,k)=>{
    const v = me.value[k]
    return n + (v==null || String(v).trim()==='' ? 1 : 0)
  },0)
})
const missingCustomCnt = computed(()=>{
  const req = fields.value.filter(f=>!!f.required)
  if (!req.length) return 0
  return req.reduce((n,f)=>{
    const raw = customVals.value[f.field_key]
    const val = raw==null ? '' : String(raw).trim()
    return n + (val ? 0 : 1)
  },0)
})
const missingTotal = computed(()=> missingFixedCnt.value + missingCustomCnt.value)
const allFilled    = computed(()=> missingTotal.value === 0)

// ステータス
const isStandard = computed(()=>{
  const p = me.value?.plan
  const exp = me.value?.plan_expiry ? new Date(me.value.plan_expiry) : null
  return p==='standard' && exp && exp > new Date()
})
const plusFilled = computed(()=>{
  const plusDefs = fields.value.filter(f=>f.category==='plus')
  if (!plusDefs.length) return true
  return plusDefs.some(f=>{
    const raw = customVals.value[f.field_key]
    const val = raw==null ? '' : String(raw).trim()
    return !!val
  })
})

// 個別フラグ
const needLciqImage = computed(()=> !me.value?.lciq_image_url)
const needVerify    = computed(()=> !me.value?.id_doc_verified)
</script>

<template>
  <div v-if="!loading && me" class="profile-checklist">
    <div v-if="needLciqImage" class="lciq-caution">
      <router-link to="/h2lciq">
        <img src="/img/lciq-logo.svg" alt="LCIQ" />
        <div class="wrap">
          <div class="head">LCIQ診断がまだ登録されていません</div>
          <p>恋愛偏差値を測定してマッチ率アップ！</p>
        </div>
      </router-link>
    </div>
    <ul>
      <li v-if="needVerify" class="verified-caution">
        <router-link to="/profile/edit">
          <div class="wrap">
            <div class="head">本人確認書類がまだ提出されていません</div>
            <p>提出をするとボカシが取れ、いいねやメッセージが送れます</p>
          </div>
        </router-link>
      </li>
      <li v-if="!allFilled" class="profile-check">
        <router-link to="/profile/edit">
          <div class="head">プロフィールを完成させるとマッチ率アップ！</div>
          <p>あと {{ missingTotal }} 項目！本当の出会いまであと少し！</p>
        </router-link>
      </li>

      <li v-if="!isStandard">
        <router-link to="/plan/checkout">
          <div class="head">スタンダード会員ではすべての機能が使えるようになります</div>
          <p>わずらわしいポイントやメッセージ制限はありません</p>
        </router-link>
      </li>

      <li v-if="!plusFilled">
        <router-link to="/plan/checkout">
          <div class="head">プラスプロフィールで、本当に合う人と出会おう</div>
          <p>出会ってから「違った」と言いにくいことは、出会う前に知っておこう</p>
        </router-link>
      </li>
    </ul>
  </div>
</template>
