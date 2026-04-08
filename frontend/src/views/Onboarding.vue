<!-- frontend/src/views/Onboarding.vue -->
<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useUser } from '@/stores/useUser'
import { GENDER_OPTIONS, SEXUAL_PREF_OPTIONS } from '@/plugins/choices'
import { api } from '@/api'
import { Cropper } from 'vue-advanced-cropper'
import 'vue-advanced-cropper/dist/style.css'
import Search from '@/views/Search.vue'

const router = useRouter()
const userStore = useUser()

const BLOODS  = ['A','B','O','AB']
const TOTAL_STEPS = 5
const step = ref(1)

const me = ref(null)
const form = ref({
  nickname: '',
  blood_type: 'A',
  gender: '',
  sexual_object_pref: '',
  date_of_birth: '',
  main_area: '渋谷',
  lciq_score: '',
})

// 誕生日：年/月/日に分けて入力
const dob = ref({ y: '1995', m: '1', d: '1' })

watch(dob, (v) => {
  const y = String(v.y || '').padStart(4, '0')
  const m = String(v.m || '').padStart(2, '0')
  const d = String(v.d || '').padStart(2, '0')
  if (v.y && v.m && v.d) {
    form.value.date_of_birth = `${y}-${m}-${d}`
  } else {
    form.value.date_of_birth = ''
  }
}, { deep: true })

const hasAvatar = ref(false)
const sending = ref(false)
const err = ref('')

// Cropper
const fileRef = ref(null)
const avatarSrc = ref('')
const cropperRef = ref(null)
const showCropper = ref(false)

// LCIQ Cropper
const lciqFileRef = ref(null)
const lciqSrc = ref('')
const lciqCropperRef = ref(null)
const showLciqCropper = ref(false)

onMounted(async () => {
  await reloadMe()
})

async function reloadMe () {
  await userStore.fetchMe()
  me.value = userStore.me
  hasAvatar.value = !!me.value?.profile_image_url
  if (me.value?.nickname) form.value.nickname = me.value.nickname
  if (me.value?.blood_type) form.value.blood_type = me.value.blood_type
  if (me.value?.gender) form.value.gender = me.value.gender
  if (me.value?.sexual_object_pref) form.value.sexual_object_pref = me.value.sexual_object_pref
  if (me.value?.date_of_birth) {
    form.value.date_of_birth = me.value.date_of_birth
    const [y, m, d] = me.value.date_of_birth.split('-')
    dob.value = { y: String(Number(y)), m: String(Number(m)), d: String(Number(d)) }
  }
  if (me.value?.main_area) form.value.main_area = me.value.main_area
  if (me.value?.lciq_score != null) form.value.lciq_score = me.value.lciq_score
}

// step1の必須チェック
const step1Valid = computed(() =>
  !!form.value.nickname?.trim() && !!form.value.sexual_object_pref
)

const canNext = computed(() => {
  if (step.value === 1) return step1Valid.value && !sending.value
  return !sending.value
})

async function next () {
  if (!canNext.value) return
  // step1を抜けるタイミングで一旦保存（必須項目）
  if (step.value === 1) {
    await saveProgress()
    if (err.value) return
  }
  step.value = Math.min(TOTAL_STEPS, step.value + 1)
}

function back () {
  step.value = Math.max(1, step.value - 1)
}

async function saveProgress () {
  sending.value = true
  err.value = ''
  try {
    const f = form.value
    const payload = {}
    if (f.nickname?.trim()) payload.nickname = f.nickname.trim()
    if (f.blood_type) payload.blood_type = f.blood_type
    if (f.gender) payload.gender = f.gender
    if (f.sexual_object_pref) payload.sexual_object_pref = f.sexual_object_pref
    if (f.date_of_birth) payload.date_of_birth = f.date_of_birth
    if (f.main_area?.trim()) payload.main_area = f.main_area.trim()
    if (f.lciq_score !== '' && f.lciq_score !== null) {
      payload.lciq_score = Number(f.lciq_score)
    }
    if (Object.keys(payload).length > 0) {
      await api.patch('me/', payload)
      await reloadMe()
    }
  } catch (e) {
    err.value = e?.response?.data?.detail || '保存に失敗しました。入力内容をご確認ください'
  } finally {
    sending.value = false
  }
}

function onAvatarChange (e) {
  const file = e.target.files?.[0]
  if (!file) return
  if (avatarSrc.value) URL.revokeObjectURL(avatarSrc.value)
  avatarSrc.value = URL.createObjectURL(file)
  showCropper.value = true
}

async function onAvatarCropSubmit () {
  const result = cropperRef.value?.getResult()
  const canvas = result?.canvas
  if (!canvas) return

  sending.value = true
  err.value = ''
  try {
    const blob = await new Promise((resolve) =>
      canvas.toBlob(resolve, 'image/jpeg', 0.9)
    )
    const fd = new FormData()
    fd.append('image', blob, 'profile.jpg')
    await api.post('me/avatar/', fd, { headers: { 'Content-Type':'multipart/form-data' } })
    hasAvatar.value = true
    await reloadMe()
    showCropper.value = false
    avatarSrc.value = ''
  } catch (e) {
    err.value = e?.response?.data?.detail || '画像アップロードに失敗しました'
  } finally {
    sending.value = false
    if (fileRef.value) fileRef.value.value = ''
  }
}

function onLciqImageChange (e) {
  const file = e.target.files?.[0]
  if (!file) return
  if (lciqSrc.value) URL.revokeObjectURL(lciqSrc.value)
  lciqSrc.value = URL.createObjectURL(file)
  showLciqCropper.value = true
}

async function onLciqCropSubmit () {
  const result = lciqCropperRef.value?.getResult()
  const canvas = result?.canvas
  if (!canvas) return

  sending.value = true
  err.value = ''
  try {
    const blob = await new Promise((resolve) =>
      canvas.toBlob(resolve, 'image/jpeg', 0.9)
    )
    const fd = new FormData()
    fd.append('image', blob, 'lciq.jpg')
    await api.post('me/lciq-image/', fd, { headers: { 'Content-Type':'multipart/form-data' } })
    await reloadMe()
    showLciqCropper.value = false
    lciqSrc.value = ''
  } catch (e) {
    err.value = e?.response?.data?.detail || 'LCIQ画像アップロードに失敗しました'
  } finally {
    sending.value = false
    if (lciqFileRef.value) lciqFileRef.value.value = ''
  }
}

async function finish () {
  await saveProgress()
  if (err.value) return
  router.push('/mypage')
}
</script>

<template>
  <!-- 裏側：本物のSearch画面（操作不可） -->
  <div class="onboarding-backdrop">
    <div class="backdrop-search">
      <Search />
    </div>
    <div class="backdrop-overlay"></div>
  </div>

  <!-- モーダル本体 -->
  <div class="onboarding-modal-wrap">
    <div class="onboarding-modal">
      <!-- ステップバー -->
      <div class="step-bar">
        <div class="step-dots">
          <div
            v-for="i in TOTAL_STEPS"
            :key="i"
            class="step-dot"
            :class="{ active: i === step, done: i < step }"
          ></div>
        </div>
        <div class="step-text small text-muted">
          <template v-if="step < TOTAL_STEPS">
            あと{{ TOTAL_STEPS - step }}ステップ
          </template>
          <template v-else>あと少し！</template>
        </div>
      </div>

      <div v-if="err" class="alert alert-danger py-2 small mb-3">{{ err }}</div>

      <!-- Step 1: ニックネーム + 性嗜好 -->
      <div v-if="step === 1" class="step-content">
        <h2 class="fw-bold fs-3 mb-1">
          はじめまして！<template v-if="me?.username"><br>{{ me.username }}さん！</template>
        </h2>
        <p class="small text-muted mb-4">まずはここだけ教えてください</p>

        <div class="mb-4">
          <label class="form-label small mb-1">ニックネーム<span class="text-danger">*</span></label>
          <div class="form-text mt-0 mb-2">本名でなくてOK。あとから変更できます。</div>
          <input class="form-control py-2" v-model.trim="form.nickname" maxlength="50" placeholder="例）たろう" />
        </div>

        <div class="mb-2">
          <label class="form-label small mb-1">性指向<span class="text-danger">*</span></label>
          <div class="form-text mt-0 mb-2">あなたが恋愛対象とする性別を教えてください。</div>
          <div class="btn-group-split">
            <template v-for="p in SEXUAL_PREF_OPTIONS" :key="p.value">
              <input
                class="btn-check"
                type="radio"
                name="sexual_object_pref"
                :id="`sexual-object-pref-${p.value}`"
                :value="p.value"
                v-model="form.sexual_object_pref"
                autocomplete="off"
              />
              <label class="btn btn-outline-primary" :for="`sexual-object-pref-${p.value}`">
                {{ p.label }}
              </label>
            </template>
          </div>
        </div>
      </div>

      <!-- Step 2: イメージ画像 -->
      <div v-else-if="step === 2" class="step-content">
        <h2 class="fw-bold fs-3 mb-1">プロフィール写真</h2>
        <p class="small text-muted mb-4">あなたを表す1枚を選んでみよう</p>

        <label class="image-uploader mx-auto d-block" style="max-width:240px">
          <img
            :src="me?.profile_image_url || '/img/noimage.jpg'"
            alt=""
            class="rounded w-100 aspect-ratio-1 object-fit-cover"
          />
          <div class="image-uploader-overlay">
            <div class="image-uploader-hint">
              <small>{{ me?.profile_image_url ? '画像を変更' : 'タップして画像を選ぶ' }}</small>
            </div>
          </div>
          <input ref="fileRef" type="file" accept="image/*" class="d-none" @change="onAvatarChange">
        </label>
      </div>

      <!-- Step 3: 性別 / 血液型 / 誕生日 / メインエリア -->
      <div v-else-if="step === 3" class="step-content">
        <h2 class="fw-bold fs-3 mb-1">基本情報</h2>
        <p class="small text-muted mb-3">分かる範囲でOK</p>

        <div class="mb-3">
          <label class="form-label small mb-1">ご自身の性別</label>
          <div class="form-text mt-0 mb-2">プロフィールに表示されます。</div>
          <div class="btn-group-split">
            <template v-for="g in GENDER_OPTIONS" :key="g.value">
              <input class="btn-check" type="radio" name="gender" :id="`gender-${g.value}`" :value="g.value" v-model="form.gender" autocomplete="off" />
              <label class="btn btn-outline-primary" :for="`gender-${g.value}`">{{ g.label }}</label>
            </template>
          </div>
        </div>

        <div class="mb-3">
          <label class="form-label small mb-1">血液型</label>
          <div class="form-text mt-0 mb-2">相性診断などで使います。</div>
          <div class="btn-group-split">
            <template v-for="b in BLOODS" :key="b">
              <input class="btn-check" type="radio" name="blood_type" :id="`blood-${b}`" :value="b" v-model="form.blood_type" autocomplete="off" />
              <label class="btn btn-outline-primary" :for="`blood-${b}`">{{ b }}</label>
            </template>
          </div>
        </div>

        <div class="mb-3">
          <label class="form-label small mb-1">誕生日</label>
          <div class="form-text mt-0 mb-2">年齢の表示に使います。半角数字で入力してください。</div>
          <div class="d-flex align-items-center gap-2">
            <input type="number" class="form-control" inputmode="numeric" v-model="dob.y" placeholder="1995" min="1900" max="2100" />
            <span class="small text-muted">年</span>
            <input type="number" class="form-control" inputmode="numeric" v-model="dob.m" placeholder="1" min="1" max="12" />
            <span class="small text-muted">月</span>
            <input type="number" class="form-control" inputmode="numeric" v-model="dob.d" placeholder="1" min="1" max="31" />
            <span class="small text-muted">日</span>
          </div>
        </div>

        <div class="mb-2">
          <label class="form-label small mb-1">メインエリア</label>
          <div class="form-text mt-0 mb-2">居住地ではなく、主に活動しているエリアを入れてください。</div>
          <input class="form-control" v-model.trim="form.main_area" placeholder="例）渋谷 / 新宿など" />
        </div>
      </div>

      <!-- Step 4: LCIQスコア -->
      <div v-else-if="step === 4" class="step-content">
        <h2 class="fw-bold fs-3 mb-1">LCIQスコア</h2>
        <p class="small text-muted mb-3">
          ６つの恋愛力を分析しあなたの恋愛偏差値©をスコアリング。
          <a href="/h2lciq" class="ms-1">LCIQとは？</a>
        </p>

        <div class="mb-3">
          <label class="form-label small">スコア</label>
          <input type="number" class="form-control" v-model="form.lciq_score" min="0" max="999" placeholder="例）120" />
        </div>

        <div>
          <label class="form-label small">診断スクリーンショット</label>
          <label class="image-uploader d-block" style="max-width:240px">
            <img
              :src="me?.lciq_image_url || '/img/noimage.jpg'"
              alt=""
              class="rounded w-100 aspect-ratio-1 object-fit-cover"
            />
            <div class="image-uploader-overlay">
              <div class="image-uploader-hint">
                <small>{{ me?.lciq_image_url ? '画像を変更' : 'タップして画像を選ぶ' }}</small>
              </div>
            </div>
            <input ref="lciqFileRef" type="file" accept="image/*" class="d-none" @change="onLciqImageChange">
          </label>
        </div>
      </div>

      <!-- Step 5: 完了 -->
      <div v-else-if="step === 5" class="step-content text-center">
        <h2 class="fw-bold fs-3 mb-2">準備完了！</h2>
        <p class="small text-muted mb-4">
          素敵な出会いがあなたを待ってます。<br>
          マイページから始めましょう。
        </p>
      </div>

      <!-- ナビゲーション -->
      <div class="step-nav mt-4">
        <button v-if="step > 1 && step < TOTAL_STEPS" type="button" class="btn btn-link text-muted" @click="back" :disabled="sending">
          戻る
        </button>
        <span v-else></span>

        <div class="d-flex gap-2">
          <button
            v-if="step >= 2 && step <= 4"
            type="button"
            class="btn btn-outline-secondary"
            @click="next"
            :disabled="sending"
          >
            あとで入力
          </button>
          <button
            v-if="step < TOTAL_STEPS"
            type="button"
            class="btn btn-primary"
            @click="next"
            :disabled="!canNext"
          >
            {{ sending ? '保存中…' : '次へ' }}
          </button>
          <button
            v-else
            type="button"
            class="btn btn-primary"
            @click="finish"
            :disabled="sending"
          >
            {{ sending ? '保存中…' : 'マイページへ' }}
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Avatar Cropper Modal -->
  <div v-if="showCropper" class="modal d-block" style="background-color: rgba(0,0,0,0.5); z-index:2000;">
    <div class="modal-dialog modal-lg">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">画像を編集</h5>
          <button type="button" class="btn-close" @click="showCropper = false"></button>
        </div>
        <div class="modal-body">
          <div v-if="avatarSrc" style="height: 400px; display: flex; align-items: center;">
            <Cropper ref="cropperRef" :src="avatarSrc" :stencil-props="{ aspectRatio: 1 }" />
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="showCropper = false" :disabled="sending">キャンセル</button>
          <button type="button" class="btn btn-primary" @click="onAvatarCropSubmit" :disabled="sending">
            {{ sending ? 'アップロード中…' : 'この画像でアップロード' }}
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- LCIQ Cropper Modal -->
  <div v-if="showLciqCropper" class="modal d-block" style="background-color: rgba(0,0,0,0.5); z-index:2000;">
    <div class="modal-dialog modal-lg">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">LCIQ画像を編集</h5>
          <button type="button" class="btn-close" @click="showLciqCropper = false"></button>
        </div>
        <div class="modal-body">
          <div v-if="lciqSrc" style="height: 400px; display: flex; align-items: center;">
            <Cropper ref="lciqCropperRef" :src="lciqSrc" :stencil-props="{ aspectRatio: null }" />
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="showLciqCropper = false" :disabled="sending">キャンセル</button>
          <button type="button" class="btn btn-primary" @click="onLciqCropSubmit" :disabled="sending">
            {{ sending ? 'アップロード中…' : 'この画像でアップロード' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>


<style scoped lang="scss">
/* 裏側：本物のSearch画面（フッターより上、操作不可） */
.onboarding-backdrop {
  position: fixed;
  top: 0; left: 0; right: 0;
  bottom: var(--footer-h);
  z-index: 1000;
  overflow: hidden;
  pointer-events: none; /* クリック無効 */
}
.backdrop-search {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}
.backdrop-search :deep(*) {
  pointer-events: none !important;
}
.backdrop-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.78);
}

/* モーダル本体 */
.onboarding-modal-wrap {
  position: fixed;
  top: 0; left: 0; right: 0;
  bottom: var(--footer-h);
  z-index: 1100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  pointer-events: none;
}
.onboarding-modal {
  pointer-events: auto;
  background: #fff;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.35);
  width: 100%;
  max-width: 460px;
  max-height: calc(100vh - 32px);
  padding: 28px 24px 22px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ステップバー */
.step-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 20px;
}
.step-dots {
  display: flex;
  gap: 6px;
  flex: 1;
}
.step-dot {
  flex: 1;
  height: 6px;
  border-radius: 3px;
  background: #e9ecef;
  transition: background 0.3s;
}
.step-dot.done { background: var(--bs-primary, #0d6efd); }
.step-dot.active { background: var(--bs-primary, #0d6efd); opacity: 0.7; }

.step-content {
  flex: 1;
  overflow: hidden;
}

.step-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

/* 画像アップローダー：画像全体がタップ可能 */
.image-uploader {
  position: relative;
  cursor: pointer;
  border-radius: 0.5rem;
  overflow: hidden;
}
.image-uploader-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.35);
  color: #fff;
  opacity: 1;
  transition: opacity 0.2s;
}
.image-uploader:hover .image-uploader-overlay {
  background: rgba(0,0,0,0.5);
}
.image-uploader-hint {
  text-align: center;
  line-height: 1.2;
}

/* ボタン群を横いっぱいで均等分割 */
.btn-group-split {
  display: flex;
  width: 100%;
  gap: 8px;
}
.btn-group-split .btn {
  flex: 1 1 0;
  min-width: 0;
}

/* flatpickr 縮小 */
:deep(.flatpickr-calendar) {
  transform: scale(0.85);
  transform-origin: top left;
  z-index: 99999 !important;
  box-shadow: none;
}
:deep(.flatpickr-calendar.arrowTop::before),
:deep(.flatpickr-calendar.arrowTop::after) {
  display: none !important;
}

.form-control.form-control-sm {
  font-size: 0.875rem;
  padding-top: 0.25rem;
  padding-bottom: 0.25rem;
}
</style>
