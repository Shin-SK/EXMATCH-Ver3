<!-- src/components/Avatar.vue -->
<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  src:      { type: String, default: '' },
  alt:      { type: String, default: '' },
  to:       { type: [String, Object], default: '' },  // 画像全体をリンクにしたい時（文字列またはルート設定）
  fallback: { type: String, default: '/img/user-unset.webp' },

  /* 表示モード：
     - fixed … 幅×高さ = size の正方形（従来の「アイコン」）
     - block … 幅100%・高さは aspect-ratio で決定（カード内フルワイド）
  */
  mode:     { type: String, default: 'fixed' },       // 'fixed' | 'block'

  // fixed用：px or '3rem'
  size:     { type: [Number, String], default: 48 },

  // block用：アスペクト比（数値 or '16/9' など）
  ratio:    { type: [Number, String], default: 1 },   // 1 = 正方形, 16/9 = 横長

  // トリミング方法
  fit:      { type: String, default: 'cover' },       // 'cover' | 'contain'

  // 角丸
  radius:   { type: String, default: 'circle' },      // 'circle' | 'rounded' | 'none'

  // 画像が小さい/未ロード時の背景
  bg:       { type: String, default: '#f5f5f5' },

  // LCP対策したい場面だけ true
  eager:    { type: Boolean, default: false },
})

const failed = ref(false)

const sizePx = computed(() =>
  typeof props.size === 'number' ? `${props.size}px` : props.size
)

// Cloudinary URL のサイズパラメータを変換
function resizeCloudinaryUrl(url, size) {
  if (!url || !url.includes('cloudinary')) return url
  const numSize = typeof size === 'number' ? size : parseInt(size) || 80
  
  // c_fill でアスペクト比を維持しつつ短辺基準でクロップ
  const transform = `w_${numSize},h_${numSize},c_fill`
  
  // 既存の w_XXX,h_XXX,c_XXX パラメータを置き換え
  if (url.match(/\/w_\d+,h_\d+(,c_\w+)?/)) {
    return url.replace(/\/w_\d+,h_\d+(,c_\w+)?\//, `/${transform}/`)
  }
  // パラメータがない場合は upload の後に追加
  if (url.includes('/upload/')) {
    return url.replace('/upload/', `/upload/${transform}/`)
  }
  return url
}

const imgSrc = computed(() => {
  failed.value = false
  const baseUrl = props.src || props.fallback
  // fixed モードの場合のみ Cloudinary URL を変換
  if (props.mode === 'fixed' && props.size) {
    return resizeCloudinaryUrl(baseUrl, props.size)
  }
  return baseUrl
})

const wrapperStyle = computed(() => {
  const style = { overflow: 'hidden', background: props.bg }
  // 角丸
  const r = props.radius
  style.borderRadius = r === 'circle' ? '50%' : r === 'rounded' ? '12px' : '0'

  if (props.mode === 'fixed') {
    style.width = sizePx.value
    style.height = sizePx.value
    style.display = 'inline-block'
  } else {
    // block
    style.width = '100%'
    // aspect-ratio は数値 or 'W/H'を許容
    const ar = typeof props.ratio === 'string' && props.ratio.includes('/')
      ? props.ratio
      : Number(props.ratio) || 1
    style.aspectRatio = ar
    style.display = 'block'
  }
  return style
})

const imgStyle = computed(() => ({
  width: '100%',
  height: '100%',
  objectFit: props.fit,          // cover でクロップ／contain で全体表示
  objectPosition: 'center center',
  display: 'block',
}))

function onError(e){
  if (failed.value) return
  failed.value = true
  e.target.onerror = null
  e.target.src = props.fallback
}
</script>

<template>
  <component :is="to ? 'router-link' : 'div'" :to="to" class="avatar-wrap" :style="wrapperStyle">
    <img
      :src="imgSrc"
      :alt="alt"
      :style="imgStyle"
      :loading="eager ? 'eager' : 'lazy'"
      draggable="false"
      @error="onError"
    />
  </component>
</template>

<style scoped>
.avatar-wrap { line-height: 0; }
</style>
