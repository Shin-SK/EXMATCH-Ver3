<!-- frontend/src/views/Onboarding.vue -->
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUser } from '@/stores/useUser'
import { GENDER_OPTIONS, SEXUAL_PREF_OPTIONS } from '@/plugins/choices'
import { api } from '@/api'

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

onMounted(async () => {
  await reloadMe()
})

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

async function onAvatarChange (e) {
  const file = e.target.files?.[0]
  if (!file) return
  const fd = new FormData()
  fd.append('image', file)
  sending.value = true
  err.value = ''
  try {
    await api.post('me/avatar/', fd, { headers: { 'Content-Type':'multipart/form-data' } })
    hasAvatar.value = true
    await reloadMe()
  } catch (e) {
    err.value = e?.response?.data?.detail || '画像アップロードに失敗しました'
  } finally {
    sending.value = false
    e.target.value = ''
  }
}

// 任意：LCIQスクショ
async function onLciqImageChange (e) {
  const file = e.target.files?.[0]
  if (!file) return
  const fd = new FormData()
  fd.append('image', file)
  sending.value = true
  err.value = ''
  try {
    await api.post('me/lciq-image/', fd, { headers: { 'Content-Type':'multipart/form-data' } })
    await reloadMe()
  } catch (e) {
    err.value = e?.response?.data?.detail || 'LCIQ画像アップロードに失敗しました'
  } finally {
    sending.value = false
    e.target.value = ''
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
  <div class="container py-4" style="max-width:720px">
    <h1 class="h3 fw-bold mb-3">初期設定</h1>
    <p class="text-muted mb-4">まずは基本情報を入力してください（※は任意）。</p>

    <div v-if="err" class="alert alert-danger">{{ err }}</div>

    <!-- 画像 -->
    <div class="card mb-3">
      <div class="card-header fw-bold">イメージ画像<span class="badge bg-danger text-white">必須</span></div>
      <div class="card-body d-flex align-items-center gap-3">
        <img
          :src="me?.profile_image_url || '/img/noimage.jpg'"
          alt=""
          class="rounded"
          style="width:100px;height:100px;object-fit:cover"
        />
        <label class="btn btn-outline-primary mb-0">
          画像を選択
          <input type="file" accept="image/*" class="d-none" @change="onAvatarChange">
        </label>
        <span class="ms-2 small" :class="hasAvatar ? 'text-success' : 'text-danger'">
          {{ hasAvatar ? 'アップロード済み' : '未アップロード' }}
        </span>
      </div>
    </div>

    <!-- 基本情報 -->
    <div class="card mb-3">
      <div class="card-header fw-bold">基本情報</div>
      <div class="card-body">
        <div class="row g-3 gy-5">
          <div class="col-md-6">
            <label class="form-label">ニックネーム<span class="badge bg-danger text-white">必須</span></label>
            <input class="form-control" v-model.trim="form.nickname" maxlength="50" />
          </div>

          <div class="col-md-6">
            <label class="form-label">血液型<span class="badge bg-danger text-white">必須</span></label>
            <select class="form-select" v-model="form.blood_type">
              <option value="" disabled>選択してください</option>
              <option v-for="b in BLOODS" :key="b" :value="b">{{ b }}</option>
            </select>
          </div>

          <div class="col-md-6">
            <label class="form-label">性別<span class="badge bg-danger text-white">必須</span></label>
            <select class="form-select" v-model="form.gender">
              <option value="" disabled>選択してください</option>
              <option v-for="g in GENDER_OPTIONS" :key="g.value" :value="g.value">
                {{ g.label }}
              </option>
            </select>
          </div>

          <div class="col-md-6">
            <label class="form-label">性指向<span class="badge bg-danger text-white">必須</span></label>
            <select class="form-select" v-model="form.sexual_object_pref">
              <option value="" disabled>選択してください</option>
              <option v-for="p in SEXUAL_PREF_OPTIONS" :key="p.value" :value="p.value">
                {{ p.label }}
              </option>
            </select>
          </div>

          <div class="col-md-6">
            <label class="form-label">誕生日<span class="badge bg-danger text-white">必須</span></label>
            <input type="date" class="form-control" v-model="form.date_of_birth" />
          </div>

          <div class="col-md-6">
            <label class="form-label">メインエリア<span class="badge bg-danger text-white">必須</span></label>
            <input class="form-control" v-model.trim="form.main_area" placeholder="例）中野区" />
            <div class="form-text">※居住地ではなく主に活動しているエリアです。</div>
          </div>
        </div>
      </div>
    </div>

	<div class="card mb-5">
		<div class="card-header">LCIQ</div>
		<div class="card-body">
			<div class="d-flex aling-center flex-column gap-1 mt-2 mb-5">
				わからなければあとから追加することも可能です。
				<a href="/h2lciq" class="btn btn-warning">LICQとは？</a>
			</div>
			<div class="row g-3 gy-5">
				<div class="col-md-6">
					<label class="form-label">LCIQスコア（任意）</label>
					<input type="number" class="form-control" v-model="form.lciq_score" min="0" max="999" />
				</div>

				<div class="col-md-6">
					<label class="form-label">LCIQ診断スクショ（任意）</label>
					<div class="d-flex align-items-center gap-2">
					<label class="btn btn-outline-secondary mb-0">
						画像を選択
						<input type="file" accept="image/*" class="d-none" @change="onLciqImageChange">
					</label>
					<img :src="me?.lciq_image_url" v-if="me?.lciq_image_url"
						style="height:48px;width:48px;object-fit:cover" class="rounded border" />
					</div>
				</div>
			</div>
		</div>
	</div>

    <div class="d-grid gap-2">
      <button class="btn btn-primary btn-lg" :disabled="!canSave" @click="saveAndGo">
        {{ sending ? '保存中…' : '保存してマイページへ' }}
      </button>
    </div>
  </div>
</template>


<style scoped lang="scss">

.form-label{
	font-size: 12px;
	display: flex;
	align-items: center;
	gap: 8px;
}

</style>