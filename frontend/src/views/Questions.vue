<!-- frontend/src/views/Questions.vue -->
<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { fetchProfileFields, fetchMyCustomFields, updateMyCustomFields } from '@/api'
import { IconLock } from '@tabler/icons-vue'

const router = useRouter()

const fields = ref([])
const plusFields = ref([])
const vals = ref({})
const loading = ref(true)
const saving = ref({})
const err = ref('')
const openKey = ref(null)
const itemRefs = ref({})

const toChoices = (v) => Array.isArray(v) ? v : (v || '').split('\n').filter(s => s.trim())
const listify = (d) => Array.isArray(d) ? d : (d?.results || d?.items || [])

onMounted(async () => {
  try {
    const [defs, custom] = await Promise.all([
      fetchProfileFields(),
      fetchMyCustomFields(),
    ])
    const all = listify(defs)
    fields.value = all.filter(f => f.category === 'normal')
    plusFields.value = all.filter(f => f.category === 'plus')

    const customVals = custom?.values || {}
    for (const f of all) {
      vals.value[f.field_key] = customVals[f.field_key] ?? ''
    }

    // 最初の未回答質問を自動で開く
    const firstUnanswered = fields.value.find(f => !vals.value[f.field_key])
    openKey.value = firstUnanswered
      ? firstUnanswered.field_key
      : fields.value[0]?.field_key ?? null
  } catch {
    err.value = '読み込みに失敗しました'
  } finally {
    loading.value = false
  }
})

function setItemRef(el, key) {
  if (el) itemRefs.value[key] = el
}

function toggleOpen(key) {
  openKey.value = openKey.value === key ? null : key
}

function goToCheckout() {
  router.push('/plan/checkout')
}

async function onSelect(fieldKey) {
  saving.value = { ...saving.value, [fieldKey]: true }
  err.value = ''

  // 回答直後に次の質問へ進む
  const currentIndex = fields.value.findIndex(f => f.field_key === fieldKey)
  const nextField = fields.value[currentIndex + 1]
  if (nextField) {
    openKey.value = nextField.field_key
    await nextTick()
    const el = itemRefs.value[nextField.field_key]
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  try {
    await updateMyCustomFields({ [fieldKey]: vals.value[fieldKey] })
  } catch {
    err.value = '保存に失敗しました'
  } finally {
    saving.value = { ...saving.value, [fieldKey]: false }
  }
}
</script>

<template>
  <div class="py-4" style="max-width: 640px;">
    <h1 class="fw-bold fs-2 mb-1">質問に答える</h1>
    <p class="text-muted small mb-4">回答が増えるほどおすすめの精度がUPします</p>

    <div v-if="loading" class="text-center py-5 text-muted">Loading...</div>

    <template v-else>
      <div v-if="err" class="alert alert-danger">{{ err }}</div>

      <!-- normalカテゴリ -->
      <div class="d-flex flex-column gap-2 mb-4">
        <div
          v-for="f in fields"
          :key="f.field_key"
          :ref="(el) => setItemRef(el, f.field_key)"
          class="border rounded overflow-hidden"
        >
          <button
            type="button"
            class="w-100 text-start p-3 bg-white border-0 d-flex align-items-center justify-content-between"
            @click="toggleOpen(f.field_key)"
          >
            <div class="d-flex align-items-center gap-2 flex-wrap">
              <span class="fw-bold small">{{ f.field_label }}</span>
              <span
                v-if="vals[f.field_key]"
                class="badge rounded-pill"
                style="background: rgba(var(--bs-primary-rgb), 0.12); color: var(--bs-primary); font-size: 0.7rem;"
              >{{ vals[f.field_key] }}</span>
            </div>
            <span
              class="text-muted ms-2 flex-shrink-0"
              :style="{ display: 'inline-block', transition: 'transform 0.2s', transform: openKey === f.field_key ? 'rotate(180deg)' : 'rotate(0deg)' }"
              style="font-size: 0.7rem;"
            >&#9660;</span>
          </button>
          <div v-show="openKey === f.field_key" class="px-3 pb-3 border-top">
            <div v-if="saving[f.field_key]" class="text-muted small py-1">保存中…</div>
            <div class="d-flex flex-wrap gap-2 pt-2">
              <template v-for="(c, i) in toChoices(f.choices)" :key="c">
                <input
                  class="btn-check"
                  type="radio"
                  :name="`q-${f.field_key}`"
                  :id="`q-${f.field_key}-${i}`"
                  :value="c"
                  v-model="vals[f.field_key]"
                  @change="onSelect(f.field_key)"
                />
                <label class="btn btn-outline-primary btn-sm" :for="`q-${f.field_key}-${i}`">
                  {{ c }}
                </label>
              </template>
            </div>
          </div>
        </div>

        <div v-if="fields.length === 0" class="text-muted text-center py-3">
          質問が見つかりませんでした
        </div>
      </div>

      <!-- plusカテゴリ（ロック表示のみ） -->
      <template v-if="plusFields.length">
        <div class="fw-bold mb-2 small text-muted">プラスプロフィール</div>
        <div class="d-flex flex-column gap-2">
          <button
            v-for="f in plusFields"
            :key="f.field_key"
            type="button"
            class="border rounded p-3 d-flex align-items-center justify-content-between bg-white border-0"
            style="cursor: pointer; text-align: left;"
            @click="goToCheckout"
          >
            <span class="fw-bold small text-muted">{{ f.field_label }}</span>
            <div class="d-flex align-items-center gap-1 text-muted" style="font-size: 0.75rem;">
              <IconLock :size="13" />
              有料会員様のみ開放
            </div>
          </button>
        </div>
      </template>
    </template>
  </div>
</template>
