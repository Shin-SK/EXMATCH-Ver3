<!-- src/views/ChatRoom.vue（全文置き換え） -->
<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api, fetchMessages, sendMessage } from '@/api'
import { useUnread } from '@/stores/useUnread'
import dayjs from 'dayjs'
import 'dayjs/locale/ja'
dayjs.locale('ja')

const route  = useRoute()
const uid    = ref(String(route.params.uid))
const unread = useUnread()

const loading   = ref(true)
const err       = ref('')
const msgs      = ref([])
const after     = ref(0)
const text      = ref('')
const composing = ref(false)
const sending   = ref(false)
let timer = null

const dstr    = (ts) => dayjs(ts).format('YYYYMMDD')
const fmtDate = (ts) => dayjs(ts).format('YYYY/MM/DD (ddd)')
const fmtTime = (ts) => dayjs(ts).format('HH:mm')
const sameDay = (a, b) => dstr(a) === dstr(b)

const partnerAvatar = ref('/img/user-unset.webp')

async function loadPartner() {
  try {
    const { data } = await api.get(`profiles/${uid.value}/`)
    partnerAvatar.value = data?.profile_image_url || '/img/user-unset.webp'
  } catch {}
}

function scrollToBottom() {
  requestAnimationFrame(() => {
    const el = document.getElementById('chat-body')
    if (el) el.scrollTop = el.scrollHeight
  })
}

function onVisibilityChange(){
  if (document.hidden) {
    if (timer) { clearInterval(timer); timer = null }
  } else {
    if (!timer) {
      loadNew()
      timer = setInterval(loadNew, 4000)
    }
  }
}

async function loadNew() {
  try {
    const rows = await fetchMessages(uid.value, after.value || 0)
    if (rows.length) {
      msgs.value.push(...rows)
      after.value = rows[rows.length - 1].id
      await unread.readThread(Number(uid.value))
      scrollToBottom()
    }
  } catch (e) {
    if (!msgs.value.length) err.value = '読み込みに失敗しました'
    console.error('[ChatRoom]', e?.response?.status, e?.response?.data || e)
  } finally {
    loading.value = false
  }
}

async function doSend() {
  const body = text.value.trim()
  if (!body || sending.value) return
  sending.value = true
  err.value = ''
  try {
    await sendMessage(uid.value, body)
    text.value = ''
    await loadNew()
  } catch (e) {
    err.value = e?.message || '送信に失敗しました'
    console.error('[ChatRoom:send]', e)
  } finally {
    sending.value = false
  }
}

function onKeydown(e) {
  if (e.isComposing || composing.value) return
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    doSend()
  }
}

onMounted(async () => {
  await Promise.all([loadPartner(), loadNew()])
  await unread.readThread(Number(uid.value))
  timer = setInterval(loadNew, 4000)
  document.addEventListener('visibilitychange', onVisibilityChange)
})
onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
  document.removeEventListener('visibilitychange', onVisibilityChange)
})

watch(() => route.params.uid, async (v) => {
  uid.value = String(v)
  msgs.value = []
  after.value = 0
  loading.value = true
  partnerAvatar.value = '/img/user-unset.webp'
  await Promise.all([loadPartner(), loadNew()])
})
</script>

<template>
  <div class="d-flex flex-column">
    <div class="h2 fw-bold my-3">メッセージ</div>

    <div id="chat-body" class="chat-body flex-fill overflow-auto rounded p-2 bg-light">
      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border" role="status"></div>
      </div>
      <div v-else-if="err" class="alert alert-danger py-2 mb-2">{{ err }}</div>

      <ul v-else class="msg-list list-unstyled m-0">
        <template v-for="(m, i) in msgs" :key="m.id">
          <!-- 日付セパレータ -->
          <li
            v-if="i===0 || !sameDay(msgs[i-1].created_at, m.created_at)"
            :key="'sep-'+dstr(m.created_at)"
            class="day-sep d-flex justify-content-center my-4"
          >
            <span class="bg-white text-dark px-4 py-1" style="border-radius: 100px;">
              {{ fmtDate(m.created_at) }}
            </span>
          </li>

          <!-- ★ 単一テンプレ + CSSのorderで左右の並びを切替 -->
          <li :class="m.is_mine ? 'me' : 'you'">
            <img v-if="!m.is_mine" class="avatar" :src="partnerAvatar" alt="avatar" />
            <div class="bubble">
              <div>{{ m.text }}</div>
            </div>
            <div class="time">{{ fmtTime(m.created_at) }}</div>
          </li>
        </template>
      </ul>
    </div>

    <div class="mt-5 position-relative">
      <textarea
        class="form-control bg-light py-4 px-2"
        rows="1"
        style="border-radius: 100px; border: none;"
        v-model="text"
        placeholder="メッセージを入力"
        @keydown="onKeydown"
        @compositionstart="composing = true"
        @compositionend="composing = false"
        :disabled="sending"
      ></textarea>
      <div class="position-absolute end-0 top-0 bottom-0 m-auto me-3" style="height: fit-content;">
        <button class="" :disabled="sending || !text.trim()" @click="doSend">
          <IconSend />
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.chat-body {
  background: #f8f9fa;
  min-height: 70vh;
  max-height: 75vh;
}

/* 行自体はflex。子要素の並びはorderで切替 */
.msg-list li {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  margin-bottom: 8px;
}

/* 要素の基本スタイル */
.avatar {
  width: 32px; height: 32px; border-radius: 50%;
  object-fit: cover; flex: 0 0 32px;
}
.bubble {
  max-width: 70%;
  padding: .5rem .75rem;
  border-radius: 1rem;
  word-break: break-word;
  background: #ffffff;
  border: 1px solid #e5e7eb;
}
.time {
  font-size: .75rem;
  opacity: .7;
  align-self: flex-end;
  line-height: 1;
  min-width: 2.5em; /* 例: 幅を少し確保してガタつき防止 */
  text-align: center;
}

.me{
  flex-direction: row-reverse;
  .avatar{
    display: none;
  }
  .time{

  }
  .bubble {
    background: #0d6efd;
    color: #fff;
    border-color: #0d6efd;
  }
}

.day-sep { text-align:center; color:#6c757d; font-size:.8rem; margin:.75rem 0; }
</style>
