<script setup>
import { ref, computed, onMounted } from 'vue'
import { createCheckout } from '@/api'
import { IconChevronsDown, IconCheck } from '@tabler/icons-vue'

onMounted(() => { document.title = 'プラン購入' })

// —— 標準プラン ——
const basePrice = 4500 // 1ヶ月の月額（比較基準）

const plans = [
  {
    key: 'standard_3m',
    title: '3ヶ月パック',
    months: 3,
    perMonth: 3850,
    total: 11550,
    discount: 14,
    bonuses: [
      { img: '/img/a-gel.png', text: '4,620円分<br>プレゼント' },
      { head: 'オープニングキャンペーン', text: '1ヶ月分<br>プレゼント' }
    ]
  },
  {
    key: 'standard_6m',
    title: '6ヶ月パック',
    months: 6,
    perMonth: 3150,
    total: 18900,
    discount: 30,
    recommended: true,
    bonuses: [
      { img: '/img/a-gel.png', text: '7,560円分<br>プレゼント' },
      { head: 'オープニングキャンペーン', text: '2ヶ月分<br>プレゼント' }
    ]
  },
  {
    key: 'standard_12m',
    title: '12ヶ月パック',
    months: 12,
    perMonth: 2450,
    total: 29400,
    discount: 46,
    bonuses: [
      { img: '/img/a-gel.png', text: '11,760円分<br>プレゼント' },
      { head: 'オープニングキャンペーン', text: '3ヶ月分<br>プレゼント' }
    ]
  },
]
const single = { key: 'standard_1m', title: '1ヶ月パック', months: 1, perMonth: 4500, total: 4500 }

const selectedPlan = ref('')

// —— 追加オプション（プラスプロフィール）——
const plusOptions = [
  { key: 'plus_1m', label: '1ヶ月', price: 750, total: 750 },
  { key: 'plus_3m', label: '3ヶ月', price: 750, total: 2250 },
  { key: 'plus_6m', label: '6ヶ月', price: 750, total: 4500 },
  { key: 'plus_12m', label: '12ヶ月', price: 750, total: 9000 },
]
const selectedPlus = ref('')

// —— 計算 ——
const selectedPlanData = computed(() => {
  if (!selectedPlan.value) return null
  if (selectedPlan.value === single.key) return single
  return plans.find(p => p.key === selectedPlan.value)
})

const selectedPlusData = computed(() => {
  if (!selectedPlus.value) return null
  return plusOptions.find(o => o.key === selectedPlus.value)
})

const orderTotal = computed(() => {
  let t = 0
  if (selectedPlanData.value) t += selectedPlanData.value.total
  if (selectedPlusData.value) t += selectedPlusData.value.total
  return t
})

const canSubmit = computed(() => !!selectedPlan.value)
const submitting = ref(false)
const err = ref('')

function formatPrice(n) {
  return n.toLocaleString()
}

async function submitCheckout() {
  if (!canSubmit.value || submitting.value) return
  submitting.value = true
  err.value = ''
  try {
    const options = selectedPlus.value ? [selectedPlus.value] : []
    const payload = { plan: selectedPlan.value, options }
    const res = await createCheckout(payload)
    const url = res?.url || res?.redirect_url
    if (url) {
      window.location.href = url
      return
    }
    console.log('[Checkout payload]', payload, res)
    alert('決済エンドポイント未接続です。バックエンドURLを合わせてください。')
  } catch (e) {
    console.error(e)
    err.value = '購入処理に失敗しました'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="upgrade-plan">
    <!-- 見出し -->
    <div class="head-set">
      <h2>PLAN</h2>
      <h3>プラン購入</h3>
    </div>

    <form @submit.prevent="submitCheckout">
      <!-- Standard plan -->
      <div class="standard">
        <p class="lead">スタンダードプランでは<br>すべての機能がご利用いただけます</p>

        <div class="standard__wrap">
          <!-- 複数パック -->
          <div
            v-for="p in plans"
            :key="p.key"
            class="box"
            :class="{ selected: selectedPlan === p.key, recommended: p.recommended }"
            @click="selectedPlan = p.key"
          >
            <div class="badge-recommend" v-if="p.recommended">おすすめ</div>
            <div class="badge-discount">{{ p.discount }}%OFF</div>

            <div class="price">
              <div class="head">{{ p.title }}</div>
              <div class="inner">
                <div class="wrap">
                  <div class="original-price">
                    <s>{{ formatPrice(basePrice) }}円/月</s>
                  </div>
                  <div class="numb">
                    {{ formatPrice(p.perMonth) }}<small>円/月</small>
                  </div>
                  <div class="savings">
                    1ヶ月プランより<strong>{{ formatPrice(basePrice - p.perMonth) }}円/月</strong>おトク
                  </div>

                  <label :class="{ active: selectedPlan === p.key }">
                    <input
                      type="radio"
                      name="plan"
                      :value="p.key"
                      v-model="selectedPlan"
                    />
                    <IconCheck v-if="selectedPlan === p.key" :size="16" />
                    {{ selectedPlan === p.key ? '選択中' : '選択する' }}
                  </label>
                </div>
              </div>

              <div class="amount">
                <span>合計</span>{{ formatPrice(p.total) }}円
              </div>
            </div>

            <!-- 特典 -->
            <div class="special">
              <div class="item agel" v-if="p.bonuses?.[0]">
                <img :src="p.bonuses[0].img" alt="" />
                <div class="text">
                  <span v-html="p.bonuses[0].text"></span>
                </div>
              </div>
              <div class="item opening" v-if="p.bonuses?.[1]">
                <div class="head">{{ p.bonuses[1].head }}</div>
                <div class="text" v-html="p.bonuses[1].text"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- 1ヶ月パック -->
        <div class="single" :class="{ selected: selectedPlan === single.key }" @click="selectedPlan = single.key">
          <div class="head">{{ single.title }}</div>
          <div class="price">
            <div class="numb">{{ formatPrice(single.perMonth) }}<span>円/月</span></div>
            <label :class="{ active: selectedPlan === single.key }">
              <input
                type="radio"
                name="plan"
                :value="single.key"
                v-model="selectedPlan"
              />
              <IconCheck v-if="selectedPlan === single.key" :size="16" />
              {{ selectedPlan === single.key ? '選択中' : '選択する' }}
            </label>
          </div>
        </div>
      </div>

      <!-- Option: Plus Profile -->
      <div class="option" id="option">
        <div class="head-set">
          <h2>PLUS PROFILE</h2>
          <h3>追加オプション</h3>
        </div>

        <p class="text-center my-4">ご要望にお答えして<br>深い部分までわかる追加オプションを導入しました</p>

        <div class="wrap">
          <!-- 左: 価格カード（割引表示） -->
          <div class="price special">
            <div class="normal">
              <div class="numb">
                1,500<span>円/月</span>
              </div>
            </div>
            <div class="arrow">
              <IconChevronsDown />
            </div>
            <div class="down">
              <div class="off">50%<br>OFF</div>
              <div class="numb">750<span>円/月</span></div>
            </div>
          </div>

          <!-- 右: 説明 -->
          <ul>
            <li>性指向がわかる</li>
          </ul>
        </div>

        <!-- カート（トグル選択） -->
        <div class="cart">
          <div class="items">
            <div
              v-for="opt in plusOptions"
              :key="opt.key"
              class="item"
              :class="{ active: selectedPlus === opt.key }"
              @click="selectedPlus = selectedPlus === opt.key ? '' : opt.key"
            >
              <div class="item-content">
                <span class="item-label">{{ opt.label }}</span>
                <span class="item-price">{{ formatPrice(opt.total) }}円</span>
              </div>
            </div>
          </div>
          <p class="cart-hint">※ オプションのみの購入はできません。プランと合わせてお選びください。</p>
        </div>
      </div>

      <!-- 注文サマリー -->
      <div class="order-summary" v-if="selectedPlan">
        <h4>ご注文内容</h4>
        <div class="summary-row">
          <span>{{ selectedPlanData?.title }}</span>
          <span>¥{{ formatPrice(selectedPlanData?.total || 0) }}</span>
        </div>
        <div class="summary-row" v-if="selectedPlusData">
          <span>プラスプロフィール {{ selectedPlusData.label }}</span>
          <span>¥{{ formatPrice(selectedPlusData.total) }}</span>
        </div>
        <div class="summary-total">
          <span>合計（税込）</span>
          <span>¥{{ formatPrice(orderTotal) }}</span>
        </div>
      </div>

      <!-- 決済ボタン（1つだけ） -->
      <div class="checkout-action">
        <button class="btn btn-primary w-100" type="submit" :disabled="!canSubmit || submitting">
          {{ submitting ? '処理中…' : canSubmit ? `${selectedPlanData?.title}で購入に進む` : 'プランを選択してください' }}
        </button>
        <p v-if="err" class="error">{{ err }}</p>
      </div>

      <!-- 無料プランとの比較（折りたたみ） -->
      <details class="free-compare">
        <summary>フリープランとの比較を見る</summary>
        <div class="free-compare__body">
          <ul>
            <li>価値観診断</li>
            <li>価値観マッチ ( 価値観による紹介 )</li>
            <li>お相手のプロフィールを見る</li>
            <li>お相手に「いいね！」をする</li>
            <li>「いいね！」をくれた方とマッチングする ( 無制限 )</li>
            <li>非表示機能</li>
            <li>初回メッセージ１通のみ</li>
          </ul>
          <p class="free-note">※ フリープランでは上記機能のみご利用いただけます（0円/月）</p>
        </div>
      </details>
    </form>
  </div>
</template>

<style scoped>
.object-fit-contain{ object-fit:contain }
</style>
