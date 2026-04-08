<!-- src/components/ProfileCard.vue -->
<script setup>
import { computed, ref, watch } from 'vue'
import { IconPencil } from '@tabler/icons-vue'

const props = defineProps({
  user: { type: Object, required: true },
  editable: { type: Boolean, default: false },
  editTo: { type: [String, Object], default: () => ({ name: 'profile-edit' }) },
  showPairs: { type: Boolean, default: true },
})

const name = computed(() => props.user?.nickname || props.user?.username || '???')
const area = computed(() => props.user?.main_area || '未設定')
const bio  = computed(() => props.user?.bio || '')

const pairs = computed(() => {
  const u = props.user
  if (!u) return []
  const bt = u.blood_type || '-'
  const gender = ({ male: '男性', female: '女性' })[u.gender] || '-'
  const target = ({ male: '男性', female: '女性' })[u.sexual_object_pref] || '-'
  const age = u.age ?? '-'
  return [
    ['年齢', age],
    ['血液型', bt],
    ['性別', gender],
    ['対象', target],
    ['メインエリア', area.value],
  ]
})

const photos = computed(() => {
  const ps = props.user?.photos || []
  if (ps.length) return ps
  // 写真がない場合のフォールバック1枚
  return [{ id: 'noimg', image_url: '/img/noimage.jpg' }]
})

const current = ref(0)
watch(photos, () => { current.value = 0 })

const mainPhoto = computed(() => photos.value[current.value] || photos.value[0])
</script>

<template>
  <div class="profile-card">
    <!-- メイン画像（fixedな名前オーバーレイ付き） -->
    <div class="profile-photos mb-3">
      <div class="main-photo">
        <img :src="mainPhoto?.image_url" alt="" />
        <div class="photo-overlay"></div>
        <div class="photo-name-area">
          <div class="photo-name">{{ name }}</div>
          <div class="photo-area">{{ area }}</div>
        </div>
      </div>

      <!-- サムネイル（複数枚あるときだけ） -->
      <div v-if="photos.length > 1" class="thumbs">
        <button
          v-for="(p, i) in photos"
          :key="p.id"
          type="button"
          class="thumb"
          :class="{ active: current === i }"
          @click="current = i">
          <img :src="p.image_url" alt="" />
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.profile-card { position: relative; }

.profile-photos {
  margin-left: calc(50% - 50vw);
  margin-right: calc(50% - 50vw);
  width: 100vw;
}

.main-photo {
  position: relative;
  width: 100%;
  aspect-ratio: 4/5;
  overflow: hidden;
  background: #111;
  border-bottom-left-radius: 24px;
  border-bottom-right-radius: 24px;
}
.main-photo img {
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
  bottom: 48px;
  color: #fff;
  text-shadow: 0 2px 8px rgba(0,0,0,0.4);
  pointer-events: none;
}
.photo-name { font-size: 1.6rem; font-weight: 700; line-height: 1.2; }
.photo-area { font-size: 0.9rem; opacity: 0.95; margin-top: 4px; }

.photo-edit-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(0,0,0,0.55);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  z-index: 2;
}
.photo-edit-btn:hover { background: rgba(0,0,0,0.75); }

/* サムネイル */
.thumbs {
  display: flex;
  gap: 8px;
  padding: 12px 16px 0;
  overflow-x: auto;
  scrollbar-width: none;
}
.thumbs::-webkit-scrollbar { display: none; }
.thumb {
  flex: 0 0 auto;
  width: 56px;
  height: 56px;
  padding: 0;
  border: 2px solid transparent;
  border-radius: 10px;
  overflow: hidden;
  background: #eee;
  cursor: pointer;
  transition: border-color .15s, transform .15s;
}
.thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.thumb.active {
  border-color: #0d6efd;
  transform: scale(1.04);
}

/* 情報エリア：メイン画像にかぶせる */
.profile-info {
  position: relative;
  margin-top: -32px;
  background: #fff;
  border-radius: 20px 20px 0 0;
  padding: 20px 16px 8px;
  box-shadow: 0 -8px 24px rgba(0,0,0,0.06);
}
</style>
