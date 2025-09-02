<!-- src/views/Login.vue -->
<script setup>
import { ref, computed } from 'vue'
import { useAuth } from '@/stores/useAuth'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const auth = useAuth()

const form = ref({
  username: route.query.username || '',
  password: ''
})
const showPw  = ref(false)
const sending = ref(false)
const err     = ref('')

const canSubmit = computed(() =>
  form.value.username && form.value.password && !sending.value
)

async function submit () {
  if (!canSubmit.value) return
  err.value = ''
  sending.value = true
  try {
    await auth.login(form.value.username, form.value.password) // dj-rest-auth /api/auth/login/
    const n = route.query.next
    const next = Array.isArray(n) ? n[0] : (n || '/mypage')
    router.push(next)
  } catch (e) {
    err.value = 'ログインに失敗しました。ユーザー名/パスワードをご確認ください。'
    console.error(e?.response?.data || e)
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <div class="container py-4" style="max-width:520px">
    <h1 class="h2 fw-bold my-3">ログイン</h1>

    <div v-if="err" class="alert alert-danger py-2">{{ err }}</div>

    <form @submit.prevent="submit" novalidate>
      <div class="mb-3">
        <label class="form-label">ユーザー名</label>
        <input
          class="form-control"
          v-model.trim="form.username"
          autocomplete="username"
          autofocus
          @keydown.enter.prevent="submit"
        />
      </div>

      <div class="mb-3">
        <label class="form-label">パスワード</label>
        <div class="input-group">
          <input
            :type="showPw ? 'text' : 'password'"
            class="form-control"
            v-model="form.password"
            autocomplete="current-password"
            @keydown.enter.prevent="submit"
          />
          <button class="btn btn-outline-secondary" type="button" @click="showPw = !showPw">
            {{ showPw ? '隠す' : '表示' }}
          </button>
        </div>
      </div>

      <button class="btn btn-primary w-100" type="submit" :disabled="!canSubmit">
        {{ sending ? 'ログイン中…' : 'ログイン' }}
      </button>
      <div class="d-flex align-items-center justify-content-center w-100">
        <a class="btn btn-link btn-sm " href="/signup">会員登録</a>
      </div>
      
    </form>
  </div>
</template>
