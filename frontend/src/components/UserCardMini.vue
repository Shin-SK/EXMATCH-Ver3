<!-- src/components/UserCardMini.vue -->
<script setup>
import { computed } from 'vue'
import Avatar from '@/components/Avatar.vue'
import { useUser } from '@/stores/useUser'

const userStore = useUser()

const props = defineProps({
  user: { type: Object, required: true },     // UserBrief（id, username, nickname, main_area, age, lciq_score, profile_image_url）
  createdAt: { type: String, default: '' },   // ISO: like.created_at
  size: { type: Number, default: 80 },        // アバターサイズ
  linkTo: { type: String, default: '' },      // プロフ詳細へのリンク（未指定なら /users/:id）
})

const name = computed(() => props.user?.nickname || props.user?.username || '???')
const area = computed(() => props.user?.main_area || '')
const age  = computed(() => props.user?.age ?? '')
const when = computed(() => (props.createdAt || '').slice(0,16).replace('T',' '))
const href = computed(() => props.linkTo || `/users/${props.user?.id}`)
const showLciq = computed(() => props.user?.lciq_score !== null && props.user?.lciq_score !== undefined)

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
  <div class="area">
    <div class="profile-feed-mini image">
      <div class="position-relative media--avatar" :class="{ 'lciq-blur': blurThisCard }">
        <Avatar :src="$avatar.user(user)" :size="size" :to="href" />
        <div v-if="showLciq" class="lciq-score position-absolute"><span>{{ user.lciq_score }}</span></div>
      </div>
    </div><!-- mini -->

    <div class="name-area d-flex flex-column gap-1">
      <span class="name-inner fw-bold">{{ name }}<span v-if="age !== '' && age !== null" class="age">({{ age }})</span></span>
        
      <div class="timestamp" style="font-size: 1rem;">
        <IconClock :size="10" />{{ when }}
      </div>
      <div class="main-area">
        <IconMapPin :size="10" />{{ area || '未設定' }}
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