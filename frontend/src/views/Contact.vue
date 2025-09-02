<script setup>
import { ref, computed } from 'vue'
import { sendContact } from '@/api'
import { useRoute } from 'vue-router'

const route = useRoute()
const form = ref({
  email: route.query.email || '',
  name:  route.query.name  || '',
  subject: 'general',
  message: '',
})
const sending = ref(false)
const ok = ref(false)
const err = ref('')

const subjects = [
  { value:'general', label:'ご意見・ご要望' },
  { value:'bug',     label:'不具合の報告' },
  { value:'billing', label:'決済/課金について' },
  { value:'other',   label:'その他' },
]

const canSubmit = computed(() =>
  form.value.email && form.value.name && form.value.message && !sending.value
)

async function submit(){
  if (!canSubmit.value) return
  sending.value = true
  err.value = ''; ok.value = false
  try {
    await sendContact({ ...form.value })
    ok.value = true
    // 必要ならフォームクリア
    // form.value.message = ''
  } catch (e) {
    err.value = '送信に失敗しました。時間をおいて再度お試しください。'
    console.error(e?.response?.data || e)
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <div class="contact-form container py-4" style="max-width:720px">
    <div class="h2 fw-bold my-3">お問い合わせ</div>

    <div v-if="ok" class="alert alert-success">送信しました。ご入力のメールアドレスに控えをお送りしました。</div>
    <div v-if="err" class="alert alert-danger">{{ err }}</div>

    <form @submit.prevent="submit" class="form">
      <div class="field mb-3">
        <label class="form-label">E-mail</label>
        <input class="form-control" type="email" v-model.trim="form.email" placeholder="例）user@example.com" required>
      </div>

      <div class="field mb-3">
        <label class="form-label">お名前</label>
        <input class="form-control" v-model.trim="form.name" placeholder="山田太郎" required>
      </div>

	<div class="field subject mb-3">
	<label class="form-label d-block">件名</label>

	<div class="btn-group flex-wrap" role="group" aria-label="subject group">
		<template v-for="s in subjects" :key="s.value">
		<input
			class="btn-check"
			type="radio"
			name="subject"
			:id="`subject-${s.value}`"
			:value="s.value"
			v-model="form.subject"
			autocomplete="off"
		/>
		<label class="btn btn-outline-primary" :for="`subject-${s.value}`">
			{{ s.label }}
		</label>
		</template>
	</div>
	</div>

      <div class="field mb-3">
        <label class="form-label">お問い合わせ内容</label>
        <textarea class="form-control" rows="6"
          v-model.trim="form.message"
          placeholder="お問い合わせ内容を入力してください"
          required></textarea>
      </div>

      <button type="submit" class="btn btn-primary" :disabled="!canSubmit">
        {{ sending ? '送信中…' : '送信' }}
      </button>
    </form>
  </div>
</template>
