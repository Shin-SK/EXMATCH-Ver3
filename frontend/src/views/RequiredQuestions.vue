<!-- frontend/src/views/RequiredQuestions.vue -->
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchProfileFields, fetchMyCustomFields, updateMyCustomFields } from '@/api'

const REQUIRED_KEYS = [
  'aftermatch',
  'meet_timing',
  'date_frequency',
  'communication_speed',
  'smoking',
  'love_language',
]

const router = useRouter()

const fields = ref([])
const vals = ref({})
const loading = ref(true)
const saving = ref(false)
const err = ref('')

const toChoices = (v) => Array.isArray(v) ? v : (v || '').split('\n').filter(s => s.trim())
const listify = (d) => Array.isArray(d) ? d : (d?.results || d?.items || [])

const allAnswered = computed(() =>
  fields.value.length > 0 && fields.value.every(f => !!vals.value[f.field_key])
)

onMounted(async () => {
  try {
    const [defs, custom] = await Promise.all([
      fetchProfileFields(),
      fetchMyCustomFields(),
    ])
    const all = listify(defs)
    fields.value = all
      .filter(f => f.category === 'normal' && REQUIRED_KEYS.includes(f.field_key))
      .sort((a, b) => REQUIRED_KEYS.indexOf(a.field_key) - REQUIRED_KEYS.indexOf(b.field_key))

    const customVals = custom?.values || {}
    for (const key of REQUIRED_KEYS) {
      vals.value[key] = customVals[key] ?? ''
    }
  } catch {
    err.value = '読み込みに失敗しました'
  } finally {
    loading.value = false
  }
})

async function onSelect(fieldKey) {
  saving.value = true
  err.value = ''
  try {
    await updateMyCustomFields({ [fieldKey]: vals.value[fieldKey] })
  } catch {
    err.value = '保存に失敗しました'
  } finally {
    saving.value = false
  }
}

function goNext() {
  if (!allAnswered.value) return
  router.push('/mypage')
}

function skip() {
  router.push('/mypage')
}
</script>

<template>
  <div class="container py-4" style="max-width: 640px;">
    <div class="head-set">
      <h2>PROFILE</h2>
      <h3>必須プロフィール</h3>
    </div>
    <p class="text-muted small mb-4">おすすめ精度を上げるため、まずはこの質問だけ答えてください</p>

    <div v-if="loading" class="text-center py-5 text-muted">Loading...</div>

    <template v-else>
      <div v-if="err" class="alert alert-danger">{{ err }}</div>

      <div class="d-flex flex-column gap-3">
        <div
          v-for="f in fields"
          :key="f.field_key"
          class="rounded-3 p-3 bg-white"
        >
          <div class="fw-bold mb-2 small">{{ f.field_label }}</div>
          <div class="d-flex flex-wrap gap-2">
            <template v-for="(c, i) in toChoices(f.choices)" :key="c">
              <input
                class="btn-check"
                type="radio"
                :name="`req-${f.field_key}`"
                :id="`req-${f.field_key}-${i}`"
                :value="c"
                v-model="vals[f.field_key]"
                @change="onSelect(f.field_key)"
              />
              <label class="btn btn-outline-primary btn-sm" :for="`req-${f.field_key}-${i}`">
                {{ c }}
              </label>
            </template>
          </div>
        </div>

        <div v-if="fields.length === 0" class="text-muted text-center py-3">
          質問が見つかりませんでした
        </div>
      </div>

      <div class="mt-4">
        <button
          class="btn btn-primary w-100 mb-2"
          :disabled="!allAnswered || saving"
          @click="goNext"
        >
          マイページへ進む
        </button>
        <button class="btn btn-link btn-sm w-100 text-muted" @click="skip">
          スキップしてマイページへ
        </button>
      </div>
    </template>
  </div>
</template>
