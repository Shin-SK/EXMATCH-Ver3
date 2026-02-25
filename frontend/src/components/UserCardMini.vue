<!-- src/components/UserCardMini.vue -->
<script setup>
import { computed } from 'vue'
import Avatar from '@/components/Avatar.vue'
import { useUser } from '@/stores/useUser'
import { IconClock, IconMapPin } from '@tabler/icons-vue'

const userStore = useUser()

const props = defineProps({
  user: { type: Object, required: true },     // UserBrief（id, username, nickname, main_area, age, lciq_score, profile_image_url）
  createdAt: { type: String, default: '' },   // ISO: like.created_at
  size: { type: Number, default: 160 },       // アバターサイズ
  width: { type: Number, default: 160 },      // カード全体の幅（px）
  linkTo: { type: String, default: '' },      // プロフ詳細へのリンク（未指定なら /users/:id）
})

const name = computed(() => props.user?.nickname || props.user?.username || '???')
const area = computed(() => props.user?.main_area || '')
const age  = computed(() => props.user?.age ?? '')
const when = computed(() => (props.createdAt || '').slice(0,16).replace('T',' '))
const href = computed(() => props.linkTo || `/users/${props.user?.id}`)
const showLciq = computed(() => props.user?.lciq_score !== null && props.user?.lciq_score !== undefined)

// アバターサイズを算出：size 指定があればそのまま、なければ width から算出（width の約 80%）
const avatarSize = computed(() => {
  if (props.size !== null) return props.size
  if (props.width !== null) return Math.round(props.width * 0.8)
  return 80  // デフォルト
})

// LCIQ
const viewerHasLciq = computed(() => {
  const me = userStore?.me || {}
  const hasImage = !!me.lciq_image_url
  // 数値/文字列どちらでも、未設定(null/undefined/空文字)以外を「スコアあり」と判定
  const hasScore = me.lciq_score !== null && me.lciq_score !== undefined && String(me.lciq_score) !== ''
  return hasImage && hasScore
})

const blurThisCard = computed(() =>
  !viewerHasLciq.value && props.user?.id !== userStore?.me?.id
)


</script>

<template>
  <!-- Djangoテンプレの構造/クラスを踏襲 -->
  <div class="area" :style="width ? { width: `${width}px` } : {}">
    <div class="profile-feed-mini image">
      <div class="position-relative media--avatar" :class="{ 'lciq-blur': blurThisCard }">
        <Avatar :src="$avatar.user(user)" :size="avatarSize" :to="href" />
        <div v-if="showLciq"
          class="lciq-score position-absolute"
          style="top: 8px; right: 0px;">
          <span class="bg-lciq text-white rounded-circle p-2 fs-5">{{ user.lciq_score }}</span>
        </div>
      </div>
    </div><!-- mini -->

    <div class="name-area d-flex flex-column gap-1">
      <span class="name-inner fw-bold">{{ name }}<span v-if="age !== '' && age !== null" class="age">({{ age }})</span></span>
        
      <div class="timestamp d-flex align-items-center gap-1">
        <IconClock :size="16" />{{ when }}
      </div>
      <div class="main-area d-flex align-items-center gap-1">
        <IconMapPin :size="16" />{{ area || '未設定' }}
      </div>
    </div>
  </div><!-- area -->

</template>

<style scoped>

.media--avatar { position: relative; }
.lciq-blur :deep(img){
  filter: blur(10px) saturate(.9);
  transform: scale(1.02);
  transition: filter .2s ease;
}

</style>