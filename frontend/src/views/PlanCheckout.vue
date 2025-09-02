<script setup>
import { ref, computed, onMounted } from 'vue'
import { createCheckout } from '@/api'

onMounted(() => { document.title = 'プラン購入' })

// —— 標準プラン（テンプレの内容をそのまま持ち込み）——
const plans = [
  {
    key: 'standard_3m',
    title: '3ヶ月パック',
    perMonth: '3,850',
    total: '11,550',
    bonuses: [
      { img: '/img/a-gel.png', text: '4,620円分プレゼント' },
      { head: 'オープニングキャンペーン', text: '1ヶ月分<br>プレゼント' }
    ]
  },
  {
    key: 'standard_6m',
    title: '6ヶ月パック',
    perMonth: '3,150',
    total: '18,900',
    bonuses: [
      { img: '/img/a-gel.png', text: '7,560円分プレゼント' },
      { head: 'オープニングキャンペーン', text: '2ヶ月分<br>プレゼント' }
    ]
  },
  {
    key: 'standard_12m',
    title: '12ヶ月パック',
    perMonth: '2,450',
    total: '29,400',
    bonuses: [
      { img: '/img/a-gel.png', text: '11,760円分プレゼント' },
      { head: 'オープニングキャンペーン', text: '3ヶ月分<br>プレゼント' }
    ]
  },
]
const single = { key:'standard_1m', title:'1ヶ月パック', perMonth:'4,500' }

const selectedPlan = ref('')

// —— 追加オプション（プラスプロフィール）——
// 元テンプレに合わせて：1ヶ月は“単独選択”（radio相当）、3/6/12は複数可
const plusOneMonth = ref(false)
const plusMulti = ref([]) // ['plus_3m','plus_6m',...]

function togglePlusOneMonth(v){
  plusOneMonth.value = v
  if (v) plusMulti.value = []
}
function togglePlusMulti(val){
  const idx = plusMulti.value.indexOf(val)
  if (idx>=0) plusMulti.value.splice(idx,1)
  else plusMulti.value.push(val)
  if (plusMulti.value.length) plusOneMonth.value = false
}

const canSubmit = computed(() => !!selectedPlan.value)
const submitting = ref(false)
const err = ref('')

async function submitCheckout(){
  if (!canSubmit.value || submitting.value) return
  submitting.value = true
  err.value = ''
  try {
    // payload 例: { plan:'standard_3m', options:['plus_3m','plus_6m'] }
    const options = [
      ...(plusOneMonth.value ? ['plus_1m'] : []),
      ...plusMulti.value
    ]
    const payload = { plan: selectedPlan.value, options }
    const res = await createCheckout(payload)
    // 想定: {url:"https://checkout.stripe.com/..."} か {redirect_url:"..."}
    const url = res?.url || res?.redirect_url
    if (url) {
      window.location.href = url
      return
    }
    // フォールバック（未実装時は内容を確認）
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

    <!-- Free plan -->
    <div class="freeplan">
      <div class="wrap">
        <div class="price">
          <div class="inner">0</div>
        </div>
        <ul>
          <li>価値観診断</li>
          <li>価値観マッチ ( 価値観による紹介 )</li>
          <li>お相手のプロフィールを見る</li>
          <li>お相手に「いいね！」をする</li>
          <li>「いいね！」をくれた方とマッチングする ( 無制限 )</li>
          <li>非表示機能</li>
          <li>初回メッセージ１通のみ</li>
        </ul>
      </div>
    </div>

    <!-- Standard plan -->
    <div class="standard">
      <p>スタンダードプランでは<br>すべての機能がご利用いただけます</p>
      <div class="option">
        プラスプロフィール（性指向など）が表示できる<br>
        <a href="#option">追加オプションはこちら</a>
      </div>

      <form @submit.prevent="submitCheckout">
        <div class="standard__wrap">
          <!-- 複数パック -->
          <div v-for="p in plans" :key="p.key" class="box">
            <div class="price">
              <div class="head">{{ p.title }}</div>
              <div class="inner">
                <div class="wrap">
                  <div class="numb">
                    {{ p.perMonth }}<span>円/月</span>
                  </div>

                  <!-- ラジオ: label直下にinput（:has用） -->
                  <label>
                    <input
                      type="radio"
                      name="plan"
                      :value="p.key"
                      v-model="selectedPlan"
                    />
                    購入
                  </label>
                </div>
              </div>

              <div class="amount">
                <span>合計</span>{{ p.total }}円
              </div>
            </div>

            <!-- 特典 -->
            <div class="special">
              <!-- A-GEL -->
              <div class="item agel" v-if="p.bonuses?.[0]">
                <img :src="p.bonuses[0].img" alt="" />
                <div class="text">
                  <span v-html="p.bonuses[0].text"></span>
                </div>
              </div>
              <!-- オープニング -->
              <div class="item opening" v-if="p.bonuses?.[1]">
                <div class="head">{{ p.bonuses[1].head }}</div>
                <div class="text" v-html="p.bonuses[1].text"></div>
              </div>
            </div>
          </div>

          <!-- 1ヶ月パック -->
          <div class="single">
            <div class="head">{{ single.title }}</div>
            <div class="price">
              <div class="numb">{{ single.perMonth }}<span>円/月</span></div>
              <label>
                <input
                  type="radio"
                  name="plan"
                  :value="single.key"
                  v-model="selectedPlan"
                />
                購入
              </label>
            </div>
          </div>
        </div>

        <!-- 決済へ -->
        <button class="btn btn-primary w-100" type="submit" :disabled="!canSubmit || submitting">
          {{ submitting ? '処理中…' : '購入に進む' }}
        </button>
      </form>
    </div>

    <!-- Option -->
    <div class="option" id="option">
      <div class="head-set">
        <h2>PLUS PROFILE</h2>
        <h3>ご要望にお答えして<br>深い部分までわかる追加オプションを導入しました</h3>
      </div>

      <div class="wrap">
        <!-- 左: 価格カード（割引表示） -->
        <div class="price special">
          <div class="normal">
            <div class="off">50%<br>OFF</div>
            <div class="wrap">
              1,500<span>円/月</span>
            </div>
          </div>
          <div class="sp">
            <div class="triangle"></div>
            <div class="numb">750<span>円/月</span></div>
          </div>
        </div>

        <!-- 右: 説明 -->
        <ul>
          <li>性指向がわかる</li>
        </ul>
      </div>

      <!-- カート（チェック群） -->
      <div class="cart">
        <div class="items">
          <!-- 1ヶ月: 単独選択 -->
          <div class="item">
            <label>
              <input
                type="checkbox"
                :checked="plusOneMonth"
                @change="togglePlusOneMonth(!plusOneMonth)"
              />
              1ヶ月パック
            </label>
          </div>

          <!-- 3/6/12ヶ月: 複数可 -->
          <div class="item">
            <label>
              <input
                type="checkbox"
                :checked="plusMulti.includes('plus_3m')"
                @change="togglePlusMulti('plus_3m')"
              />
              3ヶ月パック
            </label>
          </div>

          <div class="item">
            <label>
              <input
                type="checkbox"
                :checked="plusMulti.includes('plus_6m')"
                @change="togglePlusMulti('plus_6m')"
              />
              6ヶ月パック
            </label>
          </div>

          <div class="item">
            <label>
              <input
                type="checkbox"
                :checked="plusMulti.includes('plus_12m')"
                @change="togglePlusMulti('plus_12m')"
              />
              12ヶ月パック
            </label>
          </div>
        </div>
      </div>

      <!-- 決済へ（下部） -->
      <button class="btn btn-primary w-100" type="submit" @click="submitCheckout" :disabled="!canSubmit || submitting">
        {{ submitting ? '処理中…' : '購入に進む' }}
      </button>

      <p v-if="err" class="error">{{ err }}</p>
    </div>
  </div>
</template>


<style scoped>
.object-fit-contain{ object-fit:contain }
</style>
