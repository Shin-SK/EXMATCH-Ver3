<!-- src/components/ImageCropModal.vue
     画像アップロード前の編集モーダル: crop / zoom / rotate
     vue-advanced-cropper を使用 -->
<script setup>
import { ref, watch, onUnmounted } from 'vue'
import { Cropper } from 'vue-advanced-cropper'
import 'vue-advanced-cropper/dist/style.css'

const props = defineProps({
  /** モーダルを開閉する */
  show: { type: Boolean, default: false },
  /** 編集対象の画像ファイル (File) */
  file: { type: [File, null], default: null },
})

const emit = defineEmits(['confirm', 'cancel'])

const cropperRef = ref(null)
const imageUrl = ref('')
const rotation = ref(0)

// File → ObjectURL
watch(() => props.file, (f) => {
  if (imageUrl.value) URL.revokeObjectURL(imageUrl.value)
  rotation.value = 0
  imageUrl.value = f ? URL.createObjectURL(f) : ''
})

onUnmounted(() => {
  if (imageUrl.value) URL.revokeObjectURL(imageUrl.value)
})

function rotate(deg) {
  rotation.value = (rotation.value + deg) % 360
  cropperRef.value?.rotate(deg)
}

function zoomIn() {
  cropperRef.value?.zoom(1.2)
}
function zoomOut() {
  cropperRef.value?.zoom(0.8)
}

async function confirm() {
  const { canvas } = cropperRef.value.getResult()
  if (!canvas) return

  // 長辺を 1600px に制限
  const MAX = 1600
  let w = canvas.width, h = canvas.height
  if (w > MAX || h > MAX) {
    const ratio = Math.min(MAX / w, MAX / h)
    w = Math.round(w * ratio)
    h = Math.round(h * ratio)
  }

  // リサイズ用 canvas
  const out = document.createElement('canvas')
  out.width = w; out.height = h
  const ctx = out.getContext('2d')
  ctx.drawImage(canvas, 0, 0, w, h)

  const blob = await new Promise(resolve =>
    out.toBlob(resolve, 'image/jpeg', 0.85)
  )

  const file = new File([blob], props.file?.name || 'photo.jpg', { type: 'image/jpeg' })
  emit('confirm', file)
}

function cancel() {
  emit('cancel')
}
</script>

<template>
  <Teleport to="body">
    <div v-if="show" class="crop-overlay" @click.self="cancel">
      <div class="crop-modal">
        <div class="crop-header">
          <span class="fw-bold">画像を編集</span>
          <button type="button" class="btn-close" @click="cancel"></button>
        </div>

        <div class="crop-body">
          <Cropper
            ref="cropperRef"
            :src="imageUrl"
            :stencil-props="{ aspectRatio: 1 }"
            class="cropper"
          />
        </div>

        <div class="crop-controls">
          <button type="button" class="btn btn-outline-secondary btn-sm" @click="rotate(-90)">
            ↺ 左回転
          </button>
          <button type="button" class="btn btn-outline-secondary btn-sm" @click="rotate(90)">
            ↻ 右回転
          </button>
          <button type="button" class="btn btn-outline-secondary btn-sm" @click="zoomOut">
            − 縮小
          </button>
          <button type="button" class="btn btn-outline-secondary btn-sm" @click="zoomIn">
            + 拡大
          </button>
        </div>

        <div class="crop-footer">
          <button type="button" class="btn btn-outline-secondary" @click="cancel">キャンセル</button>
          <button type="button" class="btn btn-primary" @click="confirm">この画像を使う</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.crop-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.6);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
}
.crop-modal {
  background: #fff;
  border-radius: 12px;
  width: min(95vw, 520px);
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.crop-header {
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #eee;
}
.crop-body {
  flex: 1;
  min-height: 0;
  padding: 8px;
}
.cropper {
  width: 100%;
  height: 60vh;
  max-height: 400px;
}
.crop-controls {
  display: flex;
  gap: 8px;
  justify-content: center;
  padding: 8px 16px;
}
.crop-footer {
  padding: 12px 16px;
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  border-top: 1px solid #eee;
}
</style>
