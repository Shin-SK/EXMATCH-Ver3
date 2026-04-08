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
    form.value.message = ''
  } catch (e) {
    err.value = '送信に失敗しました。時間をおいて再度お試しください。'
    console.error(e?.response?.data || e)
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <div class="contact-page">
    <div class="head-set">
      <h2>CONTACT</h2>
      <h3>お問い合わせ</h3>
    </div>
    <div class="contact-card">
      <header class="contact-header">
        <p class="lead">ご質問・ご要望などお気軽にお寄せください。通常2〜3営業日以内にご返信いたします。</p>
      </header>

      <transition name="fade">
        <div v-if="ok" class="notice notice-success">
          送信しました。ご入力のメールアドレスに控えをお送りしました。
        </div>
      </transition>
      <transition name="fade">
        <div v-if="err" class="notice notice-error">{{ err }}</div>
      </transition>

      <form @submit.prevent="submit" class="form" novalidate>
        <div class="row">
          <div class="field">
            <label for="c-name">お名前 <span class="req">必須</span></label>
            <input id="c-name" type="text" v-model.trim="form.name" placeholder="山田 太郎" required>
          </div>
          <div class="field">
            <label for="c-email">メールアドレス <span class="req">必須</span></label>
            <input id="c-email" type="email" v-model.trim="form.email" placeholder="user@example.com" required>
          </div>
        </div>

        <div class="field">
          <label>件名 <span class="req">必須</span></label>
          <div class="chips">
            <template v-for="s in subjects" :key="s.value">
              <input
                class="chip-input"
                type="radio"
                name="subject"
                :id="`subject-${s.value}`"
                :value="s.value"
                v-model="form.subject"
              />
              <label class="chip" :for="`subject-${s.value}`">{{ s.label }}</label>
            </template>
          </div>
        </div>

        <div class="field">
          <label for="c-msg">お問い合わせ内容 <span class="req">必須</span></label>
          <textarea
            id="c-msg"
            rows="7"
            v-model.trim="form.message"
            placeholder="お問い合わせ内容をご記入ください"
            required
          ></textarea>
        </div>

        <div class="actions">
          <button type="submit" class="submit-btn" :disabled="!canSubmit">
            <span v-if="sending" class="spinner" aria-hidden="true"></span>
            {{ sending ? '送信中…' : '送信する' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.contact-page {
  height: 100%;
  background: #fff;
  padding: 32px 24px;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  overflow: hidden;
}
.contact-card {
  width: 100%;
  max-width: 880px;
  margin: 0 auto;
  padding: 0;
}
.contact-header { margin-bottom: 20px; }
.title {
  font-size: 1.75rem;
  font-weight: 700;
  color: #1a2238;
  margin: 0 0 8px;
  letter-spacing: 0.02em;
}
.lead {
  color: #6b7280;
  font-size: 0.92rem;
  line-height: 1.7;
  margin: 0;
}

.notice {
  padding: 12px 16px;
  border-radius: 10px;
  font-size: 0.9rem;
  margin-bottom: 20px;
}
.notice-success { background: #e8f7ee; color: #1a7f3e; border: 1px solid #b8e4c7; }
.notice-error   { background: #fdecec; color: #b3261e; border: 1px solid #f3c2c0; }

.form { display: flex; flex-direction: column; gap: 22px; }
.row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}
.field { display: flex; flex-direction: column; gap: 8px; }
.field label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #374151;
  display: flex;
  align-items: center;
  gap: 8px;
}
.req {
  font-size: 0.7rem;
  font-weight: 600;
  color: #fff;
  background: #ef4444;
  padding: 2px 8px;
  border-radius: 999px;
  letter-spacing: 0.04em;
}

input[type="text"],
input[type="email"],
textarea {
  width: 100%;
  border: 1.5px solid #e5e7eb;
  border-radius: 10px;
  padding: 12px 14px;
  font-size: 0.95rem;
  color: #1a2238;
  background: #fafbfc;
  transition: border-color 0.15s, background 0.15s, box-shadow 0.15s;
  font-family: inherit;
}
input:focus,
textarea:focus {
  outline: none;
  border-color: #004C71;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(0, 76, 113, 0.15);
}
textarea { resize: vertical; min-height: 140px; line-height: 1.6; }

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.chip-input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}
.chip {
  display: inline-flex;
  align-items: center;
  padding: 9px 18px;
  border-radius: 999px;
  border: 1.5px solid #e5e7eb;
  background: #fff;
  font-size: 0.85rem;
  font-weight: 500;
  color: #4b5563;
  cursor: pointer;
  transition: all 0.15s;
}
.chip:hover { border-color: #b3cfdc; color: #004C71; }
.chip-input:checked + .chip {
  background: #004C71;
  border-color: #004C71;
  color: #fff;
  box-shadow: 0 4px 12px rgba(0, 76, 113, 0.25);
}

.actions { display: flex; justify-content: flex-end; margin-top: 8px; }
.submit-btn {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 13px 36px;
  border: none;
  border-radius: 10px;
  background: linear-gradient(135deg, #004C71, #006a99);
  color: #fff;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.1s, box-shadow 0.15s, opacity 0.15s;
  box-shadow: 0 6px 18px rgba(0, 76, 113, 0.3);
}
.submit-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 8px 22px rgba(0, 76, 113, 0.38);
}
.submit-btn:active:not(:disabled) { transform: translateY(0); }
.submit-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  box-shadow: none;
}

.spinner {
  width: 14px; height: 14px;
  border: 2px solid rgba(255,255,255,0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

@media (max-width: 640px) {
  .title { font-size: 1.45rem; }
  .row { grid-template-columns: 1fr; gap: 22px; }
  .actions { justify-content: stretch; }
  .submit-btn { width: 100%; justify-content: center; }
}
</style>
