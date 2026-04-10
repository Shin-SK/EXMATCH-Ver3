<!-- src/views/UserProfileDetail.vue -->
<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Avatar from '@/components/Avatar.vue'
import ProfileCard from '@/components/ProfileCard.vue'
import {
  fetchProfile, fetchMatches, fetchLikesSent,
  likeUser, toggleBlock, createReport, touchFootprint
} from '@/api'
import { IconAlertTriangle, IconUserCheck, IconUserX } from '@tabler/icons-vue'

const route = useRoute()
const router = useRouter()
const uid = ref(String(route.params.uid))

const loading = ref(true)
const err = ref('')
const prof = ref(null)

const isMatched = ref(false)
const isLiked   = ref(false)
const isBlocked = ref(false)
const sendingLike  = ref(false)
const sendingBlock = ref(false)

const report = ref({ reason:'abuse', comment:'', anonymous:false })
const REASONS = [
  { val:'abuse',  label:'暴言・ハラスメント' },
  { val:'spam',   label:'スパム行為' },
  { val:'scam',   label:'詐欺・金銭要求' },
  { val:'harass', label:'ストーカー・しつこい連絡' },
  { val:'illegal',label:'違法・不適切コンテンツ' },
]

async function checkMatched(userId){
  const d = await fetchMatches(1, { partner_id: userId })
  const list = Array.isArray(d) ? d : (d.results || [])
  return list.length > 0
}

async function checkLiked(userId){
  const d = await fetchLikesSent(1, { to_user_id: userId })
  const list = Array.isArray(d) ? d : (d.results || [])
  return list.length > 0
}

async function load(){
  loading.value = true; err.value=''
  try{
    const [p] = await Promise.all([ fetchProfile(uid.value) ])
    prof.value = p
    touchFootprint(uid.value).catch(()=>{})
    ;[isMatched.value, isLiked.value] = await Promise.all([
      checkMatched(uid.value),
      checkLiked(uid.value),
    ])
  }catch(e){
    err.value = '読み込みに失敗しました'
    console.error('[UserProfileDetail]', e?.response?.status, e?.response?.data || e)
  }finally{
    loading.value = false
  }
}

async function doLike(){
  if (sendingLike.value) return
  sendingLike.value = true
  try{
    const r = await likeUser(uid.value)
    if(r?.matched){ router.push(`/chats/${uid.value}`) }
    else { isLiked.value = true; alert('いいねを送りました') }
  }catch(e){ alert('送信に失敗しました') }
  finally{ sendingLike.value = false }
}

function toChat(){ router.push(`/chats/${uid.value}`) }

async function doToggleBlock(){
  if (sendingBlock.value) return
  const ok = confirm(isBlocked.value ? 'ブロックを解除しますか？' : 'このユーザーをブロックしますか？')
  if(!ok) return
  sendingBlock.value = true
  try{
    const r = await toggleBlock(uid.value)
    isBlocked.value = !!r.blocked
  }catch(e){ alert('操作に失敗しました') }
  finally{ sendingBlock.value = false }
}

async function submitReport(){
  try{
    await createReport(uid.value, report.value.reason, report.value.comment || '', !!report.value.anonymous)
    alert('通報を受け付けました。ご協力ありがとうございます。')
  }catch(e){ alert('送信に失敗しました') }
}

onMounted(load)
watch(() => route.params.uid, v => { uid.value = String(v); load() })
</script>

<template>
  <div class="pb-3 profile-detail">
    <div class="head-set">
      <h2>PROFILE</h2>
      <h3>プロフィール</h3>
    </div>
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border" role="status"></div>
    </div>
    <div v-else-if="err" class="alert alert-danger">{{ err }}</div>

    <template v-else>
      <ProfileCard :user="prof" />

      <!-- アクション -->
      <div class="actions my-3">
        <button v-if="isMatched" class="btn btn-primary w-100 message" @click="toChat">
          メッセージ
        </button>
        <p v-else-if="isLiked" class="waiting text-center text-muted m-0 py-2">
          お相手からの返信をお待ちください…
        </p>
        <button v-else class="btn btn-primary w-100 like d-flex align-items-center justify-content-center gap-2" :disabled="sendingLike" @click="doLike">
          <IconHeart />{{ sendingLike ? '送信中…' : 'いいね' }}
        </button>
      </div>

      <!-- 通報・ブロック -->
      <div class="d-flex justify-content-center align-items-center gap-2 mb-2">
        <button class="btn btn-outline-secondary btn-sm" data-bs-toggle="collapse" data-bs-target="#reportBox">
          <IconAlertTriangle :size="16" /><span class="ms-1">通報</span>
        </button>
        <button class="btn btn-outline-secondary btn-sm" :disabled="sendingBlock" @click="doToggleBlock">
          <IconUserCheck v-if="isBlocked" :size="16" /><IconUserX v-else :size="16" />
          <span class="ms-1">{{ isBlocked ? 'ブロック解除' : 'ブロック' }}</span>
        </button>
      </div>

      <div id="reportBox" class="collapse mt-2">
        <form @submit.prevent="submitReport" class="report-form">
          <div class="mb-2">
            <label class="form-label fs-6">理由</label>
            <select v-model="report.reason" class="form-select" required>
              <option v-for="r in REASONS" :key="r.val" :value="r.val">{{ r.label }}</option>
            </select>
          </div>
          <div class="mb-2">
            <label class="form-label fs-6">詳細 (任意)</label>
            <textarea v-model="report.comment" class="form-control" rows="2"></textarea>
          </div>
          <div class="form-check mb-2">
            <input id="anon" class="form-check-input" type="checkbox" v-model="report.anonymous">
            <label class="form-check-label" for="anon">匿名で通報</label>
          </div>
          <button type="submit" class="btn btn-secondary btn-sm">送信</button>
        </form>
      </div>
    </template>
  </div>
</template>

<style scoped>
.profile-photos {
  margin-left: calc(50% - 50vw);
  margin-right: calc(50% - 50vw);
  width: 100vw;
  overflow: hidden;
}
.profile-photo-slide {
  position: relative;
  width: 100%;
  aspect-ratio: 4/5;
  overflow: hidden;
  background: #111;
}
.profile-photo-slide img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.photo-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to bottom, rgba(0,0,0,0) 55%, rgba(0,0,0,0.7) 100%);
  pointer-events: none;
}
.photo-name-area {
  position: absolute;
  left: 20px;
  right: 20px;
  bottom: 24px;
  color: #fff;
  text-shadow: 0 2px 8px rgba(0,0,0,0.4);
  pointer-events: none;
}
.photo-name {
  font-size: 1.6rem;
  font-weight: 700;
  line-height: 1.2;
}
.photo-area {
  font-size: 0.9rem;
  opacity: 0.95;
  margin-top: 4px;
}
.profile-photos :deep(.splide__pagination) {
  bottom: auto;
  top: 12px;
  left: 12px;
  right: 12px;
  padding: 0;
  display: flex;
  gap: 4px;
}
.profile-photos :deep(.splide__pagination__page) {
  flex: 1;
  height: 3px;
  width: auto;
  margin: 0;
  border-radius: 2px;
  background: rgba(255,255,255,0.4);
  opacity: 1;
  transform: none;
}
.profile-photos :deep(.splide__pagination__page.is-active) {
  background: #fff;
  transform: none;
}
</style>
