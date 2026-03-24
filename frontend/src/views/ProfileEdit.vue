<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import {
  fetchMe, updateMe,
  fetchProfileFields, fetchMyCustomFields, updateMyCustomFields,
  uploadAvatar, deleteAvatar,
  listVerifications, uploadVerification, deleteVerification
} from '@/api'

// 定数（API側のchoicesと揃える）
const BLOODS  = ['A','B','O','AB']
const GENDERS = ['male','female']
const PREFS   = ['male','female']

const me   = ref(null)
const busy = ref(false)
const msg  = ref('')

// 固定項目フォーム
const form = reactive({
  nickname: '',
  bio: '',
  main_area: '',
  date_of_birth: '',
  blood_type: '',
  gender: '',
  sexual_object_pref: '',
})

// カスタム項目定義＆値
const fields = ref([])                         // GET /profile-fields/
const customVals = ref({})                     // GET /me/custom-fields/ → { values:{} }
const isCheckbox = (f) => f.field_type === 'checkbox'
const isRadio    = (f) => f.field_type === 'radio'
const isSelect   = (f) => f.field_type === 'select'
const isText     = (f) => f.field_type === 'text'

// 本人確認
const verifsRaw = ref([]) // results配列
const vMap = computed(() => {
  const m = {}
  for (const v of verifsRaw.value) {
    if (!m[v.doc_type]) m[v.doc_type] = v   // 各タイプの最新1件だけ採用
  }
  return m
})
const DOCS = [
  { key:'identify', label:'身分証明書' },
  { key:'single',   label:'独身証明書' },
  { key:'income',   label:'年収証明書' },
  { key:'graduate', label:'卒業証明書' },
]

// 汎用
const listify = (d) => Array.isArray(d) ? d : (d?.results || d?.items || [])

// 初期ロード
async function loadAll() {
  busy.value = true
  try {
    const meData = await fetchMe()
    me.value = meData
    // 固定フォーム初期化
    Object.assign(form, {
      nickname: meData.nickname || '',
      bio: meData.bio || '',
      main_area: meData.main_area || '',
      date_of_birth: meData.date_of_birth || '',
      blood_type: meData.blood_type || '',
      gender: meData.gender || '',
      sexual_object_pref: meData.sexual_object_pref || '',
    })

    // 動的フィールド
    const defs = await fetchProfileFields()
    fields.value = listify(defs)

    const vals = await fetchMyCustomFields()
    customVals.value = vals?.values || {}

    for (const f of fields.value) {
      const k = f.field_key
      if (isCheckbox(f)) {
        const v = customVals.value[k]
        if (Array.isArray(v)) continue
        if (typeof v === 'string' && v.length) {
          customVals.value[k] = v.split(',').map(s => s.trim()).filter(Boolean)
        } else {
          customVals.value[k] = []
        }
      }
    }

    // 本人確認
    const vs = await listVerifications()
    verifsRaw.value = listify(vs)
  } finally {
    busy.value = false
  }
}

onMounted(loadAll)

// 保存：固定 + 動的
async function saveAll() {
  msg.value = ''
  busy.value = true
  try {
    // 固定
    await updateMe({ ...form })

    // 動的：checkboxはカンマ区切り文字列で送る（API側がstr保存のため）
    const payload = {}
    for (const f of fields.value) {
      const k = f.field_key
      let v = customVals.value[k] ?? ''
      if (isCheckbox(f)) {
        if (Array.isArray(v)) v = v.join(',')
      }
      payload[k] = v
    }
    await updateMyCustomFields(payload)

    msg.value = '保存しました'
    await loadAll()
  } catch (e) {
    msg.value = '保存に失敗しました'
    // eslint-disable-next-line no-console
    console.error(e)
  } finally {
    busy.value = false
  }
}

// アバター
async function onAvatarChange(e) {
  const f = e.target.files?.[0]
  if (!f) return
  busy.value = true
  try {
    await uploadAvatar(f)
    await loadAll()
  } finally {
    busy.value = false
    e.target.value = ''
  }
}
async function onAvatarDelete() {
  busy.value = true
  try {
    await deleteAvatar()
    await loadAll()
  } finally { busy.value = false }
}

// 本人確認：アップロード/削除
async function onVerifyChange(docKey, e) {
  const f = e.target.files?.[0]
  if (!f) return
  busy.value = true
  try {
    await uploadVerification(docKey, f)
    const vs = await listVerifications()
    verifsRaw.value = listify(vs)
  } finally {
    busy.value = false
    e.target.value = ''
  }
}
async function onVerifyDelete(pk) {
  busy.value = true
  try {
    await deleteVerification(pk)
    const vs = await listVerifications()
    verifsRaw.value = listify(vs)
  } finally { busy.value = false }
}
</script>

<template>
  <div class="py-3" v-if="me">
    <h1 class="h2 fw-bold my-3">プロフィール編集</h1>

    <div v-if="msg" class="alert alert-info py-2">{{ msg }}</div>

    <!-- アバター -->
    <div class="card mb-3">
      <div class="card-header fw-bold">プロフィール画像</div>
      <div class="card-body d-flex align-items-center gap-3">
        <img
          :src="me.profile_image_url || '/img/noimage.jpg'"
          alt=""
          class="rounded"
          style="width:100px;height:100px;object-fit:cover"
        />
        <div class="d-flex gap-2">
          <label class="btn btn-outline-primary mb-0">
            画像を選択
            <input type="file" accept="image/*" class="d-none" @change="onAvatarChange">
          </label>
          <button class="btn btn-outline-secondary" :disabled="!me.profile_image_url" @click="onAvatarDelete">
            削除
          </button>
        </div>
      </div>
    </div>

    <!-- 固定項目 -->
    <div class="card mb-3">
      <div class="card-header fw-bold">基本情報</div>
      <div class="card-body row g-3">
        <div class="col-md-6">
          <label class="form-label">ニックネーム</label>
          <input v-model="form.nickname" type="text" class="form-control">
        </div>
        <div class="col-md-6">
          <label class="form-label">居住地</label>
          <input v-model="form.main_area" type="text" class="form-control" placeholder="市区町村など">
        </div>
        <div class="col-md-6">
          <label class="form-label">性別</label>
          <select v-model="form.gender" class="form-select">
            <option value="">未設定</option>
            <option v-for="g in GENDERS" :key="g" :value="g">{{ g }}</option>
          </select>
        </div>
        <div class="col-md-6">
          <label class="form-label">対象</label>
          <select v-model="form.sexual_object_pref" class="form-select">
            <option value="">未設定</option>
            <option v-for="s in PREFS" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>
        <div class="col-md-6">
          <label class="form-label">血液型</label>
          <select v-model="form.blood_type" class="form-select">
            <option value="">未設定</option>
            <option v-for="b in BLOODS" :key="b" :value="b">{{ b }}</option>
          </select>
        </div>
        <div class="col-md-6">
          <label class="form-label">生年月日</label>
          <input v-model="form.date_of_birth" type="date" class="form-control">
        </div>
        <div class="col-12">
          <label class="form-label">自己紹介</label>
          <textarea v-model="form.bio" rows="4" class="form-control" placeholder="趣味や好きなことなど"></textarea>
        </div>
      </div>
    </div>

    <div class="px-3 pb-2 mt-4">
      <div class="d-flex align-items-center justify-content-center px-3 mb-4">
        <img style="width: 80px; height: auto;" src="/img/aoi-reco.svg" alt="あおいさんのおすすめ">
        <div class="fw-bold fs-5">
          AI仲人あおいさんの<br>
          おすすめ</div>
      </div>
      <router-link to="/questions" class="btn btn-outline-primary btn w-100">
        質問に答えて正確なおすすめを！
      </router-link>
      <p class="text-muted text-center mt-1 mb-0" style="font-size: 0.75rem;">回答が増えるほどおすすめの精度がUPします</p>
    </div>

    <!-- カスタム項目（動的） -->
    <!-- <div class="card mb-3">
      <div class="card-header fw-bold">選択項目</div>
      <div class="card-body row g-3">
        <template v-for="f in fields" :key="f.field_key">
          <div class="col-12" v-if="f.category === 'normal'">
            <label class="form-label">{{ f.field_label }}</label>

            <template v-if="isText(f)">
              <input v-model="customVals[f.field_key]" type="text" class="form-control">
            </template>

            <template v-else-if="isCheckbox(f)">
              <div class="d-flex flex-wrap gap-2">
                <template v-for="(c, i) in f.choices" :key="c">
                  <input
                    class="btn-check"
                    type="checkbox"
                    :id="`cb-${f.field_key}-${i}`"
                    :value="c"
                    v-model="customVals[f.field_key]"
                  />
                  <label class="btn btn-outline-primary" :for="`cb-${f.field_key}-${i}`">
                    {{ c }}
                  </label>
                </template>
              </div>
            </template>

            <template v-else-if="isRadio(f)">
              <div class="d-flex flex-wrap gap-2">
                <template v-for="(c, i) in f.choices" :key="c">
                  <input
                    class="btn-check"
                    type="radio"
                    :name="`f-${f.field_key}`"
                    :id="`r-${f.field_key}-${i}`"
                    :value="c"
                    v-model="customVals[f.field_key]"
                  />
                  <label class="btn btn-outline-primary" :for="`r-${f.field_key}-${i}`">
                    {{ c }}
                  </label>
                </template>
              </div>
            </template>
          </div>
        </template>
      </div>
    </div> -->

    <!-- プラスプロフィール -->
    <!-- <div class="card mb-3">
      <div class="card-header fw-bold">プラスプロフィール</div>
      <div class="card-body row g-3">
        <template v-for="f in fields" :key="f.field_key">
          <div class="col-12" v-if="f.category === 'plus'">
            <label class="form-label">{{ f.field_label }}</label>

            <template v-if="isText(f)">
              <input v-model="customVals[f.field_key]" type="text" class="form-control">
            </template>

            <template v-else-if="isSelect(f)">
              <select v-model="customVals[f.field_key]" class="form-select">
                <option value="">-----</option>
                <option v-for="c in f.choices" :key="c" :value="c">{{ c }}</option>
              </select>
            </template>

            <template v-else-if="isRadio(f)">
              <div class="d-flex flex-wrap gap-2">
                <template v-for="(c, i) in f.choices" :key="c">
                  <input
                    class="btn-check"
                    type="radio"
                    :name="`plus-${f.field_key}`"
                    :id="`plus-r-${f.field_key}-${i}`"
                    :value="c"
                    v-model="customVals[f.field_key]"
                  />
                  <label class="btn btn-outline-primary" :for="`plus-r-${f.field_key}-${i}`">
                    {{ c }}
                  </label>
                </template>
              </div>
            </template>

            <template v-else-if="isCheckbox(f)">
              <div class="d-flex flex-wrap gap-2">
                <template v-for="(c, i) in f.choices" :key="c">
                  <input
                    class="btn-check"
                    type="checkbox"
                    :id="`plus-cb-${f.field_key}-${i}`"
                    :value="c"
                    v-model="customVals[f.field_key]"
                  />
                  <label class="btn btn-outline-primary" :for="`plus-cb-${f.field_key}-${i}`">
                    {{ c }}
                  </label>
                </template>
              </div>
            </template>
          </div>
        </template>

        <p v-if="!fields.some(f => f.category === 'plus')" class="text-muted m-0">
          プラスプロフィール項目はありません。
        </p>
      </div>
    </div> -->

    <!-- 本人確認 -->
    <div class="card mb-3">
      <div class="card-header fw-bold">本人確認書類</div>
      <div class="card-body row g-4">
        <div class="col-md-6 col-lg-3" v-for="d in DOCS" :key="d.key">
          <div class="rounded-3 p-3 h-100" style="background:#f5f7f9">
            <div class="small text-muted mb-2">{{ d.label }}</div>

            <div class="ratio ratio-4x3 mb-2 bg-light rounded d-flex align-items-center justify-content-center overflow-hidden">
              <img
                v-if="vMap[d.key]?.image"
                :src="vMap[d.key].image"
                alt=""
                style="object-fit:contain; width:100%; height:100%"
              >
              <span v-else class="text-muted">未提出</span>
            </div>

            <div class="d-flex align-items-center justify-content-between">
              <span class="badge"
                    :class="{
                      'text-bg-secondary': !vMap[d.key],
                      'text-bg-warning' : vMap[d.key]?.status === 'pending',
                      'text-bg-success' : vMap[d.key]?.status === 'approved',
                      'text-bg-danger'  : vMap[d.key]?.status === 'rejected'
                    }">
                {{ vMap[d.key]?.status || 'none' }}
              </span>

              <div class="d-flex gap-2">
                <label class="btn btn-outline-primary btn-sm mb-0">
                  画像選択
                  <input type="file" accept="image/*" class="d-none" @change="e => onVerifyChange(d.key, e)">
                </label>
                <button
                  v-if="vMap[d.key] && vMap[d.key].status === 'pending'"
                  class="btn btn-outline-secondary btn-sm"
                  @click="onVerifyDelete(vMap[d.key].id)">
                  削除
                </button>
              </div>
            </div>
          </div>
        </div>

        <p class="text-muted mt-2 mb-0">※ JPG/PNG をアップロードしてください。</p>
      </div>
    </div>

    <div class="d-grid">
      <button class="btn btn-primary" :disabled="busy" @click="saveAll">
        {{ busy ? '保存中…' : '保存する' }}
      </button>
    </div>
  </div>

  <div v-else class="container py-5 text-center">
    <div class="spinner-border" role="status"></div>
  </div>
</template>
