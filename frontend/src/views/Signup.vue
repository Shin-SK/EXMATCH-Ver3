<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { register } from '@/api'

const router = useRouter()
const route  = useRoute()

const form = ref({
  username: '',
  email: route.query.email || '',
  password1: '',
  password2: '',
})
const show = ref({ p1:false, p2:false })
const sending = ref(false)
const ok = ref(false)
const err = ref('')
const fieldErr = ref({})  // { username: ['...'], ... }

const canSubmit = computed(() =>
  form.value.username && form.value.email && form.value.password1 && form.value.password2 && !sending.value
)

async function submit(){
  if (!canSubmit.value) return
  sending.value = true
  ok.value = false
  err.value = ''
  fieldErr.value = {}
  try {
    await register({ ...form.value })
    ok.value = true
    // そのままログインへ誘導（メール確認があるならこのままが自然）
    setTimeout(() => {
      router.push({ name:'login', query: { email: form.value.email } })
    }, 800)
  } catch (e) {
    // dj-rest-auth は {field: ["error", ...]} 形式を返す
    const data = e?.response?.data || {}
    fieldErr.value = data
    err.value = data?.detail || '登録に失敗しました。入力内容をご確認ください。'
    // console.error(data)
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <div class="container py-4" style="max-width:520px">
    <h1 class="h2 fw-bold my-3">新規登録</h1>

    <div v-if="ok" class="alert alert-success">
      登録メールを送信しました。メールの案内に従って確認を完了してください。
    </div>
    <div v-if="err" class="alert alert-danger">{{ err }}</div>

    <form @submit.prevent="submit" novalidate>
      <div class="mb-3">
        <label class="form-label">ユーザー名</label>
        <input class="form-control" v-model.trim="form.username" autocomplete="username" />
        <div v-if="fieldErr.username" class="text-danger small mt-1">
          <div v-for="(m,i) in fieldErr.username" :key="i">{{ m }}</div>
        </div>
      </div>

      <div class="mb-3">
        <label class="form-label">E-mail</label>
        <input class="form-control" type="email" v-model.trim="form.email" autocomplete="email" />
        <div v-if="fieldErr.email" class="text-danger small mt-1">
          <div v-for="(m,i) in fieldErr.email" :key="i">{{ m }}</div>
        </div>
      </div>

      <div class="mb-3">
        <label class="form-label">パスワード</label>
        <div class="input-group">
          <input :type="show.p1 ? 'text' : 'password'" class="form-control" v-model="form.password1" autocomplete="new-password" />
          <button class="btn btn-outline-secondary" type="button" @click="show.p1=!show.p1">
            {{ show.p1 ? '隠す' : '表示' }}
          </button>
        </div>
        <div v-if="fieldErr.password1" class="text-danger small mt-1">
          <div v-for="(m,i) in fieldErr.password1" :key="i">{{ m }}</div>
        </div>
      </div>

      <div class="mb-3">
        <label class="form-label">パスワード（確認）</label>
        <div class="input-group">
          <input :type="show.p2 ? 'text' : 'password'" class="form-control" v-model="form.password2" autocomplete="new-password" />
          <button class="btn btn-outline-secondary" type="button" @click="show.p2=!show.p2">
            {{ show.p2 ? '隠す' : '表示' }}
          </button>
        </div>
        <div v-if="fieldErr.password2" class="text-danger small mt-1">
          <div v-for="(m,i) in fieldErr.password2" :key="i">{{ m }}</div>
        </div>
      </div>

      <button class="btn btn-primary w-100" type="submit" :disabled="!canSubmit">
        {{ sending ? '登録中…' : '登録する' }}
      </button>
    </form>

    <p class="text-muted small mt-3">
      登録ボタンを押すことで、利用規約とプライバシーポリシーに同意したものとみなされます。
    </p>
  </div>
</template>
