<!-- src/components/UserCard.vue（スライダー部だけ置換） -->
<script setup>
import { computed } from 'vue'
import Avatar from '@/components/Avatar.vue'
import { Splide, SplideSlide } from '@splidejs/vue-splide'
import '@splidejs/splide/css'
import { useUser } from '@/stores/useUser'
import { IconCheck } from '@tabler/icons-vue'

const userStore = useUser()
const props = defineProps({
  user: { type: Object, required: true },
  pfvs: { type: Array, default: () => [] },
  matched: { type: Boolean, default: false },
  liked: { type: Boolean, default: false },
  linkTo: { type: String, default: '' },
  avatarSize: { type: Number, default: 96 },
  placeholders: { type: Boolean, default: false }, // ← 追加（一覧では false 推奨）
})

const emit = defineEmits(['like','message','open'])

const name = computed(() => props.user?.nickname || props.user?.username || '???')
const area = computed(() => props.user?.main_area || '')
const bio  = computed(() => props.user?.bio || '')
const lciqScore = computed(() => props.user?.lciq_score ?? null)
const lciqImg   = computed(() => props.user?.lciq_image_url || '')
const modalId = computed(() => `lciq-modal-${props.user?.id ?? 'x'}`) // ★ユニークID
const hasOption = computed(() => !!props.user?.option_expiry)
const badge = computed(() => props.user?.verification_badge || '')

// UserCard.vue
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


const href = computed(() => props.linkTo || `/users/${props.user?.id}`)
</script>

<template>
  <div class="box d-flex flex-column justify-content-between user-card" :class="{'option-user': hasOption}">
    <div class="box__wrap">
      <div class="slide-area position-relative">
        <Splide
          :options="{
            type: 'loop',
            perPage: 1,
            arrows: true,
            pagination: true,
            drag: true,
            autoplay: false,
            rewind: true,
            speed: 350
            /* heightRatioは使わずCSSのaspect-ratioで制御 */
          }"
          aria-label="プロフィール画像スライダー"
          class="rounded-3"
        >
          <!-- slide: avatar -->
        <SplideSlide>
          <div class="media media--avatar" :class="{ 'lciq-blur': blurThisCard }">
            <Avatar
              :src="$avatar.user(user)"
              mode="block"
              ratio="4/3"
              fit="cover"
              radius="none"
              :to="`/users/${user.id}`"
              class="check-badge"
              :class="badge ? `check-badge--${badge}` : 'check-badge--none'"
            />
          </div>
        </SplideSlide>

          <!-- slide: LCIQ（実画像があるときだけ） -->
          <SplideSlide v-if="lciqImg">
            <button
              type="button"
              class="media media--lciq p-0 border-0 bg-transparent"
              data-bs-toggle="modal"
              :data-bs-target="'#' + modalId"
              aria-label="LCIQ画像を拡大"
            >
              <img :src="lciqImg" alt="LCIQ スクリーンショット" loading="lazy" />
            </button>
          </SplideSlide>
        </Splide>
        <div v-if="lciqScore !== null" class="lciq-score bg-lciq position-absolute fs-2 p-2">
          <span>{{ lciqScore }}</span>
        </div>
        <!-- オーバーレイ -->
        <div class="absolute-area">
          <div class="text-area">
            <div class="name d-flex align-items-center">
              {{ name }}
              <span class="ms-2"><IconMapPin :size="16" class="me-1"/>{{ area }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 以下そのまま -->
      <div class="info-area">
        <div class="profile-list" v-if="pfvs && pfvs.length">
          <div class="wrap">
            <div v-for="(pfv, i) in pfvs" :key="i" class="item">
              <div class="value">{{ pfv.value }}</div>
            </div>
          </div>
        </div>
        <div class="profile-list" v-else-if="placeholders">
          <div class="wrap">
            <div class="item unset">プロフィール未入力</div>
          </div>
        </div>
        <div class="bio" v-if="bio">
          <p>{{ bio }}</p>
        </div>
        <div class="bio" v-else-if="placeholders">
          <p class="unset">自己紹介未入力</p>
        </div>
      </div>
    </div>

    <div class="btn__area">
      <button v-if="matched" class="btn btn-pink text-white w-100 d-flex align-items-center justify-content-center gap-1" @click="emit('message', user.id)">
        <IconSend />メッセージ
      </button>
      <button v-else-if="liked" class="btn btn-outline-secondary w-100 d-flex align-items-center justify-content-center gap-1" disabled>
        <IconCheck />いいねしました！
      </button>
      <button v-else class="btn btn-primary w-100 d-flex align-items-center justify-content-center gap-1" @click="emit('like', user.id)">
        <IconHeart />いいね
      </button>
    </div>
  </div>

  <!-- モーダル本体：テンプレ最後あたりに追加 -->
  <div class="modal fade" :id="modalId" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered modal-fullscreen-sm-down modal-xl p-3">
      <div class="modal-content bg-light position-relative">
        <div class="border-0 position-absolute end-0 top-0 bottom-0 m-auto me-3 mt-3" style="z-index: 9999999;">
          <button type="button" class="btn-close ms-auto" data-bs-dismiss="modal" aria-label="閉じる"></button>
        </div>
        <div class="modal-body d-flex align-items-center justify-content-center p-0 m-0 w-100">
          <img :src="lciqImg" alt="LCIQ画像" class="img-fluid w-100 d-block m-auto" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Splideの器 */
.slide-area :deep(.splide__track){ overflow:hidden; border-radius:12px; }


/* 画像の収まり：小さければ中央・大きければリサイズ。はみ出し防止 */
.media img{
  max-width:100%;
  max-height:100%;
  width:auto;
  height:auto;
  object-fit: cover; /* 塗りつぶしたいなら cover に変更 */
  object-position: center;
  aspect-ratio: 4/3;
}

/* Avatar面は背景透過でもOKなら好みで */
.media--avatar{ background:transparent; }

/* オーバーレイ（既存） */
.absolute-area{ position:absolute; inset:auto 0 0 0; padding:.5rem .75rem; pointer-events:none; }


.media--avatar { position: relative; }
.lciq-blur :deep(img){
  filter: blur(10px) saturate(.9);
  transform: scale(1.02);
  transition: filter .2s ease;
}


.user-card{
  .lciq-score{
    position: absolute;
    top: 4px;
    right: 4px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    color:white;
    font-size: 0.8rem;
  }
}

</style>
