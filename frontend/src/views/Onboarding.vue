<!-- frontend/src/views/Onboarding.vue -->
<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useUser } from '@/stores/useUser'
import { GENDER_OPTIONS, SEXUAL_PREF_OPTIONS } from '@/plugins/choices'
import { api } from '@/api'
import { Cropper } from 'vue-advanced-cropper'
import 'vue-advanced-cropper/dist/style.css'
import flatpickr from 'flatpickr'
import { Japanese } from 'flatpickr/dist/l10n/ja.js'

const router = useRouter()
const userStore = useUser()

// API側のchoicesと合わせる（ProfileEdit.vueと同じ）
const BLOODS  = ['A','B','O','AB']

const me = ref(null)
const form = ref({
  nickname: '',
  blood_type: '',
  gender: '',
  sexual_object_pref: '',
  date_of_birth: '',
  main_area: '',
  lciq_score: '',   // 任意
})

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

// Flatpickr

const dateInputRef = ref(null)
const dobCalendarRef = ref(null)
let fp = null

onMounted(async () => {
  await reloadMe()

  fp = flatpickr(dateInputRef.value, {
    locale: Japanese,
    dateFormat: 'Y-m-d',
    inline: true,
    appendTo: dobCalendarRef.value,
    maxDate: new Date(),
    defaultDate: form.value.date_of_birth || null,
    onChange: (_, dateStr) => {
      form.value.date_of_birth = dateStr
    },
  })

  // APIから入った初期値をカレンダー側にも反映
  if (form.value.date_of_birth) {
    fp.setDate(form.value.date_of_birth, false, 'Y-m-d')
  }
})

onBeforeUnmount(() => fp?.destroy())

async function reloadMe () {
  await userStore.fetchMe()
  me.value = userStore.me
  hasAvatar.value = !!me.value?.profile_image_url
  form.value.nickname = me.value?.nickname || ''
  form.value.blood_type = me.value?.blood_type || ''
  form.value.gender = me.value?.gender || ''
  form.value.sexual_object_pref = me.value?.sexual_object_pref || ''
  form.value.date_of_birth = me.value?.date_of_birth || ''
  form.value.main_area = me.value?.main_area || ''
  form.value.lciq_score = me.value?.lciq_score ?? ''
}

const canSave = computed(() => {
  const f = form.value
  return hasAvatar.value
    && f.nickname?.trim()
    && f.blood_type
    && f.gender
    && f.sexual_object_pref
    && f.date_of_birth
    && f.main_area?.trim()
    && !sending.value
})

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

// 任意：LCIQスクショ
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

async function saveAndGo () {
  if (!canSave.value) return
  sending.value = true
  err.value = ''
  try {
    // 任意の lciq_score は空文字なら送らない
    const payload = {
      nickname: form.value.nickname?.trim(),
      blood_type: form.value.blood_type,
      gender: form.value.gender,
      sexual_object_pref: form.value.sexual_object_pref,
      date_of_birth: form.value.date_of_birth,
      main_area: form.value.main_area?.trim(),
    }
    if (form.value.lciq_score !== '' && form.value.lciq_score !== null) {
      payload.lciq_score = Number(form.value.lciq_score)
    }
    await api.patch('me/', payload)
    await reloadMe()
    if (userStore.me?.is_profile_complete) {
      router.push('/mypage')
    }
  } catch (e) {
    err.value = e?.response?.data?.detail || '保存に失敗しました。入力内容をご確認ください'
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <div class="py-5" style="max-width:720px">
    <h1 class="fw-bold fs-1 mb-2">初期設定</h1>
    <p class="mb-4 small">
      あなたのことを知ってもらいましょう！
    </p>

    <div v-if="err" class="alert alert-danger">{{ err }}</div>

    <!-- 基本情報 -->
    <div class="mb-3">
      <div>
        <div class="row g-2 gy-4">
          <div class="col-md-6">
            <label class="form-label small">イメージ画像<span class="text-danger">*</span></label>
            <div class="wrap df-center gap-3 position-relative">
              <img
                :src="me?.profile_image_url || '/img/noimage.jpg'"
                alt=""
                class="rounded w-100 h-100 aspect-ratio-1 object-fit-cover w-md-50"
              />
              <div class="wrap position-absolute bottom-0 end-0 translate-middle-x mb-2">
                <label class="btn btn-sm bg-white rounded-3">
                  <IconUpload class="" />
                  <input ref="fileRef" type="file" accept="image/*" class="d-none" @change="onAvatarChange">
                </label>
              </div>
            </div>
          </div>
          <div class="col-md-6">
            <label class="form-label small">ニックネーム<span class="text-danger">*</span></label>
            <input class="form-control py-2" v-model.trim="form.nickname" maxlength="50" />
          </div>

          <div class="col-md-6">
            <label class="form-label small">
              血液型<span class="text-danger">*</span>
            </label>

            <div class="d-flex flex-wrap gap-2">
              <template v-for="b in BLOODS" :key="b">
                <input
                  class="btn-check"
                  type="radio"
                  name="blood_type"
                  :id="`blood-${b}`"
                  :value="b"
                  v-model="form.blood_type"
                  autocomplete="off"
                  required
                />
                <label class="btn btn-outline-primary" :for="`blood-${b}`">
                  {{ b }}
                </label>
              </template>
            </div>
          </div>

          <div class="col-md-6">
            <label class="form-label small">性別<span class="text-danger">*</span></label>
            <div class="d-flex flex-wrap gap-2">
              <template v-for="g in GENDER_OPTIONS" :key="g.value">
                <input
                  class="btn-check"
                  type="radio"
                  name="gender"
                  :id="`gender-${g.value}`"
                  :value="g.value"
                  v-model="form.gender"
                  autocomplete="off"
                  required
                />
                <label class="btn btn-outline-primary" :for="`gender-${g.value}`">
                  {{ g.label }}
                </label>
              </template>
            </div>
          </div>

          <div class="col-md-6">
            <label class="form-label small">性指向<span class="text-danger">*</span></label>
            <div class="d-flex flex-wrap gap-2">
              <template v-for="p in SEXUAL_PREF_OPTIONS" :key="p.value">
                <input
                  class="btn-check"
                  type="radio"
                  name="sexual_object_pref"
                  :id="`sexual-object-pref-${p.value}`"
                  :value="p.value"
                  v-model="form.sexual_object_pref"
                  autocomplete="off"
                  required
                />
                <label class="btn btn-outline-primary" :for="`sexual-object-pref-${p.value}`">
                  {{ p.label }}
                </label>
              </template>
            </div>
          </div>

          <div class="col-md-6">
            <label class="form-label small">誕生日<span class="text-danger">*</span></label>
            
            <!-- カレンダーをここに出す（上） -->
            <div ref="dobCalendarRef" class="mb-2"></div>
            
            <!-- input を下に置く（小さめ） -->
            <input
              ref="dateInputRef"
              type="text"
              class="form-control form-control-sm w-auto"
              style="min-width: 160px;"
              placeholder="YYYY-MM-DD"
              readonly
            />
          </div>

          <div class="col-md-6">
            <label class="form-label small">メインエリア<span class="text-danger">*</span></label>
            <input class="form-control" v-model.trim="form.main_area" placeholder="例）渋谷 / 新宿など" />
            <div class="form-text">※居住地ではなく主に活動しているエリアです。</div>
          </div>
        </div>
      </div>
    </div>

	<div class="bg-white shadow-sm p-3 py-4 rounded">
		<div class="mb-4">
      <div class="fw-bold fs-2 mb-2">LCIQスコア</div>
          <small class="d-block">６つの恋愛力を分析し<br>あなたの恋愛偏差値&copy;をスコアリングします。</small>
          <a href="/h2lciq" class="btn btn-sm btn-link m-0 p-0">LICQとは？</a>
    </div>
		<div class="">
			<div class="row g-3 gy-3">
				<div class="col-md-6">
					<label class="form-label small">LCIQスコア</label>
					<input type="number" class="form-control" v-model="form.lciq_score" min="0" max="999" />
				</div>
				<div class="col-md-6">
					<label class="form-label small">LCIQ診断スクリーンショット</label>
					<div class="df-center position-relative">
            <img 
              :src="me?.lciq_image_url"
              v-if="me?.lciq_image_url"
              class="rounded w-100 h-100 aspect-ratio-1 object-fit-cover"
            />
            <label class="btn btn-sm bg-white rounded-3 position-absolute bottom-0 end-0 translate-middle-x mb-2">
              <IconUpload />
              <input ref="lciqFileRef" type="file" accept="image/*" class="d-none" @change="onLciqImageChange">
            </label>
					</div>
				</div>
			</div>
		</div>
	</div>

  <small class="text-muted mb-5 mt-1 d-block">
      内容は全て後から変更可能です。※は必須項目です。
  </small>

    <div class="wrap">
      <button class="btn btn-primary w-100" :disabled="!canSave" @click="saveAndGo">
        {{ sending ? '保存中…' : '保存してマイページへ' }}
      </button>
    </div>

    <!-- Avatar Cropper Modal -->
    <div v-if="showCropper" class="modal d-block" style="background-color: rgba(0,0,0,0.5);">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">画像を編集</h5>
            <button type="button" class="btn-close" @click="showCropper = false"></button>
          </div>
          <div class="modal-body">
            <div v-if="avatarSrc" style="height: 400px; display: flex; align-items: center;">
              <Cropper
                ref="cropperRef"
                :src="avatarSrc"
                :stencil-props="{ aspectRatio: 1 }"
              />
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showCropper = false" :disabled="sending">
              キャンセル
            </button>
            <button type="button" class="btn btn-primary" @click="onAvatarCropSubmit" :disabled="sending">
              {{ sending ? 'アップロード中…' : 'この画像でアップロード' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- LCIQ Cropper Modal -->
    <div v-if="showLciqCropper" class="modal d-block" style="background-color: rgba(0,0,0,0.5);">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">LCIQ画像を編集</h5>
            <button type="button" class="btn-close" @click="showLciqCropper = false"></button>
          </div>
          <div class="modal-body">
            <div v-if="lciqSrc" style="height: 400px; display: flex; align-items: center;">
              <Cropper
                ref="lciqCropperRef"
                :src="lciqSrc"
                :stencil-props="{ aspectRatio: null }"
              />
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showLciqCropper = false" :disabled="sending">
              キャンセル
            </button>
            <button type="button" class="btn btn-primary" @click="onLciqCropSubmit" :disabled="sending">
              {{ sending ? 'アップロード中…' : 'この画像でアップロード' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>


<style scoped lang="scss">

/* flatpickrを少し縮小（全体） */
.flatpickr-calendar {
  transform: scale(0.95);
  transform-origin: top left;
  z-index: 99999 !important;
}

/* inputをさらに小さく */
.form-control.form-control-sm {
  font-size: 0.875rem;
  padding-top: 0.25rem;
  padding-bottom: 0.25rem;
}

/* 上向き矢印（arrowTop）を消す */
.flatpickr-calendar.arrowTop::before,
.flatpickr-calendar.arrowTop::after {
  display: none !important;
}

</style>