<!-- src/components/ProfileChecklist.vue -->
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchMe, fetchProfileFields, fetchMyCustomFields } from '@/api'
import {
  IconChevronRight,
  IconCheck,
  IconChevronDown,
  IconChartBar,
  IconShieldCheck,
  IconUserEdit,
  IconCrown,
  IconHeartPlus,
} from '@tabler/icons-vue'

const router = useRouter()

const loading = ref(true)
const me = ref(null)
const fields = ref([])
const customVals = ref({})

const REQUIRED_FIXED = ['nickname','gender','main_area','sexual_object_pref','lciq_score','date_of_birth']

async function loadAll(){
  loading.value = true
  try{
    const [m, defs, vals] = await Promise.all([fetchMe(), fetchProfileFields(), fetchMyCustomFields()])
    me.value = m
    fields.value = Array.isArray(defs?.items) ? defs.items : (defs?.results || [])
    customVals.value = vals?.values || {}
  } finally { loading.value = false }
}
onMounted(loadAll)

const missingFixedCnt = computed(() => {
  if (!me.value) return 0
  return REQUIRED_FIXED.reduce((n,k)=>{
    const v = me.value[k]
    return n + (v==null || String(v).trim()==='' ? 1 : 0)
  },0)
})
const missingCustomCnt = computed(()=>{
  const req = fields.value.filter(f=>!!f.required)
  if (!req.length) return 0
  return req.reduce((n,f)=>{
    const raw = customVals.value[f.field_key]
    const val = raw==null ? '' : String(raw).trim()
    return n + (val ? 0 : 1)
  },0)
})
const missingTotal = computed(()=> missingFixedCnt.value + missingCustomCnt.value)
const allFilled    = computed(()=> missingTotal.value === 0)

const isStandard = computed(()=>{
  const p = me.value?.plan
  const exp = me.value?.plan_expiry ? new Date(me.value.plan_expiry) : null
  return p==='standard' && exp && exp > new Date()
})
const plusFilled = computed(()=>{
  const plusDefs = fields.value.filter(f=>f.category==='plus')
  if (!plusDefs.length) return true
  return plusDefs.some(f=>{
    const raw = customVals.value[f.field_key]
    const val = raw==null ? '' : String(raw).trim()
    return !!val
  })
})

// 全タスク定義（ベネフィットを前面に・done判定 + モーダル詳細）
const tasks = computed(() => [
  {
    key: 'verify',
    icon: IconShieldCheck,
    title: 'ぼかしを外す',
    sub: '本人確認書類を提出',
    done: !!me.value?.id_doc_verified,
    detail: '本人確認をするとプロフィール画像のボカシが外れ、いいねやメッセージのやり取りができるようになります。',
    ctaLabel: '提出する',
    to: '/profile/edit',
  },
  {
    key: 'lciq',
    icon: IconChartBar,
    title: 'マッチ率を上げる',
    sub: 'LCIQ診断を登録',
    done: !!me.value?.lciq_image_url,
    detail: '6つの恋愛力を分析して、あなたの恋愛偏差値©︎をスコアリング。診断するとマッチ率がぐっと上がります。',
    ctaLabel: '診断について見る',
    to: '/h2lciq',
  },
  {
    key: 'profile',
    icon: IconUserEdit,
    title: 'もっと自分を知ってもらう',
    sub: 'プロフィールを完成させる',
    done: allFilled.value,
    detail: `あと ${missingTotal.value} 項目で完成です。プロフィールが充実しているほど、あなたに合った相手が見つかりやすくなります。`,
    ctaLabel: '入力する',
    to: '/profile/edit',
  },
  {
    key: 'plus',
    icon: IconHeartPlus,
    title: '本当に合う人と出会う',
    sub: 'プラスプロフィールを書く',
    done: plusFilled.value,
    detail: '「違った」と言いにくいことは、出会う前に知っておくのが一番。本当に合う人と出会うためのプロフィールです。',
    ctaLabel: '入力する',
    to: '/profile/edit',
  },
  {
    key: 'standard',
    icon: IconCrown,
    title: '制限なく使う',
    sub: 'スタンダード会員になる',
    done: isStandard.value,
    detail: 'すべての機能が制限なしで使えるようになります。わずらわしいポイントやメッセージ制限はありません。',
    ctaLabel: 'プランを見る',
    to: '/plan/checkout',
  },
])

const totalCount = computed(() => tasks.value.length)
const doneCount  = computed(() => tasks.value.filter(t => t.done).length)
const percent    = computed(() => Math.round(doneCount.value / totalCount.value * 100))

// 円グラフ用
const RADIUS = 28
const CIRCUM = 2 * Math.PI * RADIUS
const dashOffset = computed(() => CIRCUM * (1 - percent.value / 100))

// アコーディオン開閉
const expanded = ref(false)
function toggle () { expanded.value = !expanded.value }

// スルッと開く高さアニメ
function onEnter (el) {
  el.style.height = '0'
  el.style.opacity = '0'
  // 強制reflow
  void el.offsetHeight
  el.style.height = el.scrollHeight + 'px'
  el.style.opacity = '1'
}
function onAfterEnter (el) {
  el.style.height = 'auto'
}
function onLeave (el) {
  el.style.height = el.scrollHeight + 'px'
  void el.offsetHeight
  el.style.height = '0'
  el.style.opacity = '0'
}

// モーダル
const selected = ref(null)
function openTask (t) {
  if (t.done) return
  selected.value = t
}
function closeTask () { selected.value = null }
function goTask () {
  if (!selected.value) return
  const to = selected.value.to
  closeTask()
  router.push(to)
}
</script>

<template>
  <div v-if="!loading && me" class="profile-checklist">
    <!-- 進捗ヘッダー（アコーディオントリガー） -->
    <button type="button" class="checklist-header" :aria-expanded="expanded" @click="toggle">
      <div class="ring-wrap">
        <svg viewBox="0 0 64 64" class="ring">
          <circle cx="32" cy="32" :r="RADIUS" class="ring-bg" />
          <circle
            cx="32" cy="32" :r="RADIUS"
            class="ring-fg"
            :stroke-dasharray="CIRCUM"
            :stroke-dashoffset="dashOffset"
            transform="rotate(-90 32 32)"
          />
        </svg>
        <div class="ring-text">
          <div class="ring-percent">{{ percent }}<small>%</small></div>
        </div>
      </div>
      <div class="header-text">
        <div class="fw-bold">プロフィール充実度</div>
        <div class="small text-muted">
          <template v-if="doneCount === totalCount">すべて完了！素晴らしい 🎉</template>
          <template v-else>あと <strong>{{ totalCount - doneCount }}</strong> 個でコンプリート</template>
        </div>
      </div>
      <IconChevronDown :size="20" class="header-chevron" :class="{ open: expanded }" />
    </button>

    <!-- TODOリスト（アコーディオン展開） -->
    <Transition
      name="accordion"
      @enter="onEnter"
      @after-enter="onAfterEnter"
      @leave="onLeave"
    >
    <ul v-show="expanded" class="task-list">
      <li
        v-for="t in tasks"
        :key="t.key"
        class="task-item"
        :class="{ done: t.done }"
        @click="openTask(t)"
      >
        <div class="task-icon">
          <IconCheck v-if="t.done" :size="18" />
          <component v-else :is="t.icon" :size="18" />
        </div>
        <div class="task-title">
          <div>{{ t.title }}</div>
          <div class="task-sub small text-muted">{{ t.sub }}</div>
        </div>
        <IconChevronRight v-if="!t.done" :size="18" class="task-chevron" />
      </li>
    </ul>
    </Transition>

    <!-- 詳細モーダル -->
    <div v-if="selected" class="task-modal-backdrop" @click.self="closeTask">
      <div class="task-modal">
        <button type="button" class="btn-close-x" @click="closeTask" aria-label="閉じる">×</button>
        <div class="task-modal-icon">
        <component :is="selected.icon" :size="40" />
      </div>
        <h3 class="fw-bold fs-4 mb-2">{{ selected.title }}</h3>
        <p class="text-muted small mb-4">{{ selected.detail }}</p>
        <button type="button" class="btn btn-primary w-100" @click="goTask">
          {{ selected.ctaLabel }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.profile-checklist {
  padding: 0;
}

/* ヘッダー（進捗リング・アコーディオントリガー） */
.checklist-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 4px;
  width: 100%;
  background: none;
  border: none;
  text-align: left;
  cursor: pointer;
}
.header-chevron {
  color: #adb5bd;
  flex-shrink: 0;
  transition: transform 0.25s ease;
}
.header-chevron.open { transform: rotate(180deg); }
.ring-wrap {
  position: relative;
  width: 64px;
  height: 64px;
  flex-shrink: 0;
}
.ring {
  width: 100%;
  height: 100%;
}
.ring-bg {
  fill: none;
  stroke: #e9ecef;
  stroke-width: 6;
}
.ring-fg {
  fill: none;
  stroke: var(--bs-primary, #0d6efd);
  stroke-width: 6;
  stroke-linecap: round;
  transition: stroke-dashoffset 0.6s ease;
}
.ring-text {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.ring-percent {
  font-size: 1.05rem;
  font-weight: 700;
  small { font-size: 0.65rem; font-weight: 600; margin-left: 1px; }
}
.header-text { flex: 1; min-width: 0; }

/* TODOリスト */
.task-list {
  list-style: none;
  margin: 0;
  padding: 0;
  overflow: hidden;
}

/* アコーディオン slide */
.accordion-enter-active,
.accordion-leave-active {
  transition: height 0.35s cubic-bezier(0.25, 0.8, 0.3, 1),
              opacity 0.25s ease;
  overflow: hidden;
}

/* タスク行を順番にフェードイン */
.task-item {
  animation: none;
}
.accordion-enter-active .task-item {
  opacity: 0;
  transform: translateY(-4px);
  animation: task-in 0.35s ease forwards;
}
@for $i from 1 through 8 {
  .accordion-enter-active .task-item:nth-child(#{$i}) {
    animation-delay: #{0.05 + $i * 0.04}s;
  }
}
@keyframes task-in {
  to { opacity: 1; transform: translateY(0); }
}
.task-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 4px;
  border-top: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background 0.15s;
}
.task-item:hover { background: #fafafa; }
.task-item.done {
  cursor: default;
  .task-title { color: #adb5bd; text-decoration: line-through; }
}
.task-icon {
  width: 36px; height: 36px;
  border-radius: 50%;
  background: #f5f5f5;
  color: #495057;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.task-item.done .task-icon {
  background: var(--bs-primary, #0d6efd);
  color: #fff;
}
.task-sub { line-height: 1.2; margin-top: 1px; }
.task-item.done .task-sub { color: #ced4da !important; }
.task-title {
  flex: 1;
  font-size: 0.95rem;
  font-weight: 500;
}
.task-chevron { color: #ced4da; flex-shrink: 0; }

/* モーダル */
.task-modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.6);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}
.task-modal {
  position: relative;
  background: #fff;
  border-radius: 20px;
  padding: 32px 24px 24px;
  width: 100%;
  max-width: 380px;
  text-align: center;
  box-shadow: 0 20px 60px rgba(0,0,0,0.35);
}
.task-modal-icon {
  width: 72px; height: 72px;
  border-radius: 50%;
  background: #f5f5f5;
  color: var(--bs-primary, #0d6efd);
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 12px;
}
.btn-close-x {
  position: absolute;
  top: 8px; right: 12px;
  background: none;
  border: none;
  font-size: 1.5rem;
  line-height: 1;
  color: #adb5bd;
  cursor: pointer;
}
</style>
