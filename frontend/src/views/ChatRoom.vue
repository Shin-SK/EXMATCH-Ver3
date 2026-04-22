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

// 簡易可変ポーリング（setTimeout 連鎖）
const BASE_INTERVAL = 4000
const MAX_INTERVAL  = 12000
let pollInterval = BASE_INTERVAL
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

function stopTimer() {
  if (timer) { clearTimeout(timer); timer = null }
}

function scheduleNext() {
  stopTimer()
  timer = setTimeout(async () => {
    timer = null
    if (document.hidden) return
    const hadNew = await loadNew()
    pollInterval = hadNew
      ? BASE_INTERVAL
      : Math.min(pollInterval + BASE_INTERVAL, MAX_INTERVAL)
    if (!document.hidden) scheduleNext()
  }, pollInterval)
}

function startTimer() {
  stopTimer()
  pollInterval = BASE_INTERVAL
  scheduleNext()
}

async function onVisibilityChange(){
  if (document.hidden) {
    stopTimer()
  } else if (!timer) {
    pollInterval = BASE_INTERVAL
    await loadNew()
    scheduleNext()
  }
}

async function loadNew() {
  try {
    const rows = await fetchMessages(uid.value, after.value || 0)
    if (rows.length) {
      msgs.value.push(...rows)
      after.value = rows[rows.length - 1].id
      // 相手からの新着のみ既読化（自分の送信では叩かない）
      const hasFromPartner = rows.some(r => !r.is_mine)
      if (hasFromPartner) {
        unread.readThread(Number(uid.value)).catch(e => {
          console.warn('[ChatRoom] readThread failed', uid.value, e?.response?.status, e?.response?.data || e)
        })
      }
      scrollToBottom()
      return true
    }
    return false
  } catch (e) {
    if (!msgs.value.length) err.value = '読み込みに失敗しました'
    console.error('[ChatRoom] loadNew failed', e?.response?.status, e?.response?.data || e)
    return false
  } finally {
    loading.value = false
  }
}

async function doSend() {
  const body = text.value.trim()
  if (!body || sending.value) return
  sending.value = true
  err.value = ''

  // 楽観的更新：送信即時に仮表示
  const tempId = `tmp-${Date.now()}-${Math.random().toString(36).slice(2,7)}`
  const optimistic = {
    id: tempId,
    _tempId: tempId,
    text: body,
    is_mine: true,
    created_at: new Date().toISOString(),
    pending: true,
  }
  msgs.value.push(optimistic)
  text.value = ''
  scrollToBottom()

  try {
    const real = await sendMessage(uid.value, body)
    const idx = msgs.value.findIndex(m => m._tempId === tempId)
    if (idx >= 0) msgs.value.splice(idx, 1, { ...real })
    if (real?.id && real.id > after.value) after.value = real.id
    pollInterval = BASE_INTERVAL  // アクティビティ直後は最短間隔へ
  } catch (e) {
    const idx = msgs.value.findIndex(m => m._tempId === tempId)
    if (idx >= 0) msgs.value[idx] = { ...msgs.value[idx], pending: false, failed: true }
    const code = e?.detail_code || ''
    const ERR_MAP = {
      FIRST_MESSAGE_ONLY: '初回の1通のみ送信できます。スタンダードプランに加入すると継続してメッセージを送れます。',
      BLOCKED: 'このユーザーとはメッセージのやり取りができません。',
      NG_WORD: '不適切な表現が含まれているため送信できません。',
      TEXT_TOO_LONG: 'メッセージは2000文字以内にしてください。',
      REQUIRED_TEXT: 'メッセージ本文を入力してください。',
    }
    err.value = ERR_MAP[code] || e?.message || '送信に失敗しました'
    console.error('[ChatRoom:send]', code || e)
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
  // 初回1回だけ既読化
  unread.readThread(Number(uid.value)).catch(e => {
    console.warn('[ChatRoom] initial readThread failed', uid.value, e?.response?.status, e?.response?.data || e)
  })
  startTimer()
  document.addEventListener('visibilitychange', onVisibilityChange)
})
onBeforeUnmount(() => {
  stopTimer()
  document.removeEventListener('visibilitychange', onVisibilityChange)
})

watch(() => route.params.uid, async (v) => {
  stopTimer()
  uid.value = String(v)
  msgs.value = []
  after.value = 0
  loading.value = true
  partnerAvatar.value = '/img/user-unset.webp'
  await Promise.all([loadPartner(), loadNew()])
  unread.readThread(Number(uid.value)).catch(() => {})
  startTimer()
})
</script>

<template>
  <div class="d-flex flex-column">
    <div class="head-set">
      <h2>MESSAGE</h2>
      <h3>トーク</h3>
    </div>

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
          <li :class="[m.is_mine ? 'me' : 'you', { pending: m.pending, failed: m.failed }]">
            <img v-if="!m.is_mine" class="avatar" :src="partnerAvatar" alt="avatar" />
            <div class="bubble">
              <div>{{ m.text }}</div>
            </div>
            <div class="time">
              <template v-if="m.failed">送信失敗</template>
              <template v-else-if="m.pending">送信中…</template>
              <template v-else>{{ fmtTime(m.created_at) }}</template>
            </div>
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

.pending .bubble { opacity: .6; }
.failed .bubble  { opacity: .8; border-color: #dc3545; }
.failed .time    { color: #dc3545; }

.day-sep { text-align:center; color:#6c757d; font-size:.8rem; margin:.75rem 0; }
</style>
