<!-- src/views/MyPage.vue -->
<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  fetchMe, fetchMatches, fetchLikesReceived, fetchLikesSent,
  fetchProfileFields, fetchMyCustomFields,
  fetchRecommendations,
} from '@/api'
import { useProfiles } from '@/stores/useProfiles'
import { useAuth } from '@/stores/useAuth'
import UserCardMini from '@/components/UserCardMini.vue'
import UserCard from '@/components/UserCard.vue'
import ProfileCard from '@/components/ProfileCard.vue'
import ProfileChecklist from '@/components/ProfileChecklist.vue'
import { uniqById } from '@/utils/uniq'
import {
  IconHeart, IconPencil,
  IconZoomCheck, IconBrandTinder, IconChevronDown,
  IconPaw, IconMail, IconConfetti, IconProgressHelp,
} from '@tabler/icons-vue'

const me = ref(null)
const matched = ref([])
const likesTop = ref([])
const likeCount = ref(0)
const likesSentTop = ref([])
const likesSentCount = ref(0)
const completeness = ref({ percent: 0, answered: 0, total: 0 })
const loading = ref(true)
const err = ref('')
const activeTab = ref('matched')  // navタブの選択状態
const href = { name: 'profile-edit' }  // Avatarリンク先
const profiles = useProfiles()

const auth = useAuth()
const doLogout = async () => { await auth.logout(); location.href = '/login' }

// おすすめ
const recos = ref([])
const recoLoading = ref(false)
const recoErr = ref('')
const recoTop = computed(() => recos.value.slice(0, 6))

onMounted(async () => {
  loading.value = true
  recoLoading.value = true
  try {
    const [meData, mData, lData, lSentData, fields, custom, recoItems] = await Promise.all([
      fetchMe(),
      fetchMatches(1),
      fetchLikesReceived(1),
      fetchLikesSent(1).catch(() => ({ results: [], count: 0 })),
      fetchProfileFields(),
      fetchMyCustomFields(),
      fetchRecommendations().catch(() => { recoErr.value = 'おすすめの取得に失敗しました'; return [] }),
    ])
    me.value = meData

    // 必須項目の充足率計算用
    const fieldsArr = Array.isArray(fields) ? fields : (fields?.results ?? [])
    const customObj = Array.isArray(custom)
      ? Object.fromEntries(custom.map(x => [x.field_key, x.value]))
      : (custom || {})

    // --- マッチ相手：Profile(フラット)をストアへ取り込み → 参照を統一 ---
    const partners = (mData.results || []).map(r => r.partner).filter(Boolean)
    profiles.ingestList(partners)
    matched.value = profiles.getMany(partners.map(p => p.id))

    // --- いいね受信：件数とトップ6（必要ならプロフも取り込み） ---
    likeCount.value = (lData?.count ?? (lData.results?.length || 0))
    likesTop.value  = (lData.results || []).slice(0, 6)
    profiles.ingestList(likesTop.value.map(x => x.from_user).filter(Boolean))

    // --- いいね送信：件数とトップ6 ---
    likesSentCount.value = (lSentData?.count ?? (lSentData.results?.length || 0))
    likesSentTop.value = (lSentData.results || []).slice(0, 6)
    profiles.ingestList(likesSentTop.value.map(x => x.to_user).filter(Boolean))

    // --- プロフ充実度 ---
    const reqKeys  = fieldsArr.filter(f => f.required).map(f => f.field_key)
    const answered = reqKeys.filter(k => !!customObj[k]).length
    const total    = reqKeys.length || 1
    completeness.value = { percent: Math.round((answered/total)*100), answered, total }

    // --- おすすめ：items をそのまま保持（compat_score/compat_reasons を残す） ---
    recos.value = recoItems
  } catch (e) {
    err.value = '読み込みに失敗しました'
    console.error('[MyPage]', e?.response?.status, e?.response?.data || e)
  } finally {
    loading.value = false
    recoLoading.value = false
  }
})


</script>

<template>
  <div id="mypage" class="mypage">
    <div class="head-set">
      <h2>MY PAGE</h2>
      <h3>マイページ</h3>
    </div>
    <div v-if="loading">Loading...</div>
    <div v-else-if="err">{{ err }}</div>

    <template v-else>
      <section class="profile mb-0" v-if="me">
        <ProfileCard :user="me" :editable="true" :edit-to="href" :show-pairs="false" />
        <div class="first-area row g-1 border-top border-bottom py-3 mx-0">
          <div class="col-4">
            <div class="lciq-box area d-flex flex-column align-items-center flex-column h-100">
              <div class="box numb position-relative">
                <div class="fw-bold p-2" style="font-size: 2rem;">{{ me.lciq_score ?? me.lciq ?? '-' }}</div>
                  <router-link
                    class="position-absolute"
                    :to="{ name:'profile-edit' }"
                    style="top: -8px; right: -8px;">
                    <IconPencil :size="16" />
                  </router-link>
              </div>
              <div class="df-start gap-1 flex-column">
                  <div class="fw-bold small lh-1">LCIQ</div>
                <router-link class="btn btn-sm btn-link d-flex align-items-center p-0 m-0" :to="{ name:'h2lciq' }">再診断</router-link>
              </div>
            </div>
          </div>
          <div class="col-4">
            <div class="like-box area d-flex flex-column align-items-center flex-column h-100">
              <div class="numb position-relative df-center">
                <div class="fw-bold p-2" style="font-size: 2rem;">{{ likeCount }}</div>
                <router-link
                  class="position-absolute"
                  :to="{ name:'liked' }"
                  style="top: -8px; right: -8px;"><IconZoomCheck :size="16" />
                </router-link>
              </div>
              <div class="df-start flex-column gap-1">
                <div class="fw-bold small lh-1">いいね</div>
                <router-link class=" btn btn-link btn-sm p-0 m-0" :to="{ name:'liked' }" >確認する</router-link>
              </div>
            </div>
          </div>
          <div class="col-4">
            <div class="area d-flex flex-column align-items-center flex-column h-100">
              <div class="numb position-relative df-center">
                <div class="fw-bold p-2" style="font-size: 2rem;">{{ completeness.percent }}<span style="font-size: 1rem;">%</span></div>
                <router-link
                  class="position-absolute"
                  :to="{ name:'profile-edit' }"
                  style="top: -8px; right: -8px;">
                  <IconPencil :size="16" />
                </router-link>
              </div>
              <div class="df-start flex-column gap-1">
                <div class="fw-bold small lh-1">プロフ充実度</div>
                <div class="point">{{ completeness.answered }} / {{ completeness.total }}</div>
              </div>
            </div>
          </div>
        </div>
      </section>


      <section class="checklist mb-0">
        <ProfileChecklist />
      </section>

      <!-- あおいさんのおすすめ -->
      <section class="recos py-3">
        <div class="d-flex align-items-center justify-content-center px-3 mb-4">
          <img style="width: 80px; height: auto;" src="/img/aoi-reco.svg" alt="あおいさんのおすすめ">
          <div class="fw-bold fs-5">
            AI仲人あおいさんの<br>
            おすすめ</div>
        </div>

        <div v-if="recoLoading" class="text-center py-3 text-muted">Loading...</div>
        <div v-else-if="recoErr" class="px-3 text-danger small">{{ recoErr }}</div>

        <template v-else-if="recoTop.length">
          <div class="reco-scroll d-flex gap-3 overflow-x-auto px-3 pb-2">
            <div
              v-for="item in recoTop"
              :key="item.id"
              class="reco-card flex-shrink-0"
              style="cursor:pointer;"
              @click="$router.push('/users/' + item.id)"
            >
              <UserCardMini
                :user="item"
                :width="160"
                :size="160"
                :link-to="`/users/${item.id}`"
              />
              <div v-if="item.compat_score != null" class="text-center mt-1">
                <span class="badge bg-secondary" style="font-size:.7rem;">{{ item.compat_score }}%</span>
              </div>
              <div v-if="item.compat_reasons && item.compat_reasons.length" class="small text-muted text-center mt-1" style="font-size:.65rem; line-height:1.3;">
                {{ item.compat_reasons.slice(0, 3).map(r => r.label || r).join(' / ') }}
              </div>
            </div>
          </div>
        </template>

        <div v-else class="px-3 py-2">
          <p class="text-muted small mb-2">おすすめを作成中です。プロフィールを埋めるほど精度が上がります。</p>
          <router-link :to="{ name: 'profile-edit' }" class="btn btn-sm btn-outline-primary">プロフィールを編集</router-link>
        </div>

        <div class="px-3 pb-2 mt-4">
          <router-link to="/questions" class="btn btn-outline-primary btn-sm w-100">
            もっと質問に答えて正確なおすすめを！
          </router-link>
          <p class="text-muted text-center mt-1 mb-0" style="font-size: 0.75rem;">回答が増えるほどおすすめの精度がUPします</p>
        </div>

      </section>


      <nav class="tab-nav d-flex gap-2 mb-3" aria-label="マイページタブ">
        <button
          type="button"
          :class="['tab-btn', { active: activeTab === 'matched' }]"
          @click="activeTab = 'matched'">
          <IconBrandTinder />マッチ
          <span v-if="matched.length" class="badge">{{ matched.length }}</span>
        </button>
        <button
          type="button"
          :class="['tab-btn', { active: activeTab === 'likes' }]"
          @click="activeTab = 'likes'">
          もらった<IconHeart />
          <span v-if="likeCount" class="badge">{{ likeCount }}</span>
        </button>
        <button
          type="button"
          :class="['tab-btn', { active: activeTab === 'likes-sent' }]"
          @click="activeTab = 'likes-sent'">
          した<IconHeart />
          <span v-if="likesSentCount" class="badge">{{ likesSentCount }}</span>
        </button>
      </nav>

      <section class="matched" id="matched" v-show="activeTab === 'matched'">
        <!-- <div class="head-title">マッチしたユーザー</div> -->
        <div class="area">
          <template v-if="matched.length">
            <div class="feed">
              <UserCard
                v-for="u in matched"
                :key="u.id"
                :user="u"
                :pfvs="[]"
                :matched="true"
                :placeholders="false"
                @message="$router.push('/chats/' + u.id)"
                @open="$router.push('/users/' + u.id)"
              />
            </div>
          </template>
          <div v-else class="d-flex justify-content-center align-items-center w-100" style="height: 20vh;">
            <router-link to="/users">出会いはすぐそこに</router-link>
          </div>
        </div>
      </section>

        <!-- 置換: likesTop の描画 -->
      <section class="followed" id="followed" v-show="activeTab === 'likes'">
        <!-- <div class="head-title">いいねしてくれたユーザー</div> -->
        <div class="area">
            <template v-if="likesTop.length">
              <div class="feed feed-mini">
                <UserCardMini
                  v-for="like in likesTop"
                  :key="like.id"
                  :user="like.from_user"
                  :created-at="like.created_at"
                  :link-to="`/users/${like.from_user?.id}`"
                />
              </div>
              <p class="more text-center">
                <router-link to="/likes/received">一覧を見る<IconChevronRight :size="16" /></router-link>
              </p>
            </template>
            <div v-else class="d-flex justify-content-center align-items-center w-100" style="height: 20vh;">
              <router-link to="/users">出会いはすぐそこに</router-link>
            </div>
          </div>

      </section>

      <!-- いいねした -->
      <section class="followed" id="likes-sent" v-show="activeTab === 'likes-sent'">
        <div class="area">
            <template v-if="likesSentTop.length">
              <div class="feed feed-mini">
                <UserCardMini
                  v-for="like in likesSentTop"
                  :key="like.id"
                  :user="like.to_user"
                  :created-at="like.created_at"
                  :link-to="`/users/${like.to_user?.id}`"
                />
              </div>
              <p class="more text-center">
                <router-link to="/likes/sent">一覧を見る<IconChevronRight :size="16" /></router-link>
              </p>
            </template>
            <div v-else class="d-flex justify-content-center align-items-center w-100" style="height: 20vh;">
              <router-link to="/users">まだいいねしていません</router-link>
            </div>
          </div>
      </section>

      <!-- 折りたたみ①: プロフィール詳細 -->


      <!-- 折りたたみ②: 契約情報 -->


      <section class="menu">
        <ul>
          <li>
            <button
              class="menu-btn"
              data-bs-toggle="collapse"
              data-bs-target="#profile-area"
              aria-expanded="false"
              aria-controls="profile-area">
              <span>あなたのプロフィール</span><IconChevronDown />
            </button>
            <div class="collapse" id="profile-area">
              <div class="area">
                <div class="box">
                  <div class="head">自己紹介</div>
                  <div class="text">{{ me?.bio || '未設定' }}</div>
                </div>
                <div class="box grid grid-cols-[150px_1fr]">
                  <div class="head">年齢</div>
                  <div class="text">{{ me?.age ?? '未設定' }}</div>
                </div>
                <div class="box grid grid-cols-[150px_1fr]">
                  <div class="head">血液型</div>
                  <div class="text">{{ me?.blood_type || '未設定' }}</div>
                </div>
                <div class="box grid grid-cols-[150px_1fr]">
                  <div class="head">性別</div>
                  <div class="text">{{ ({male:'男性',female:'女性'})[me?.gender] || '未設定' }}</div>
                </div>
                <div class="box grid grid-cols-[150px_1fr]">
                  <div class="head">対象</div>
                  <div class="text">{{ ({male:'男性',female:'女性'})[me?.sexual_object_pref] || '未設定' }}</div>
                </div>
                <div class="box grid grid-cols-[150px_1fr]">
                  <div class="head">メインエリア</div>
                  <div class="text">{{ me?.main_area || '未設定' }}</div>
                </div>
              </div>
            </div>
          </li>
          <li>
            <button
              class="menu-btn"
              data-bs-toggle="collapse"
              data-bs-target="#user-area"
              aria-expanded="false"
              aria-controls="user-area">
              <span>ユーザー情報</span><IconChevronDown />
            </button>
            <div class="collapse" id="user-area">
              <div class="area">
                <div class="box grid grid-cols-[150px_1fr]">
                  <div class="head">プラン</div>
                  <div class="text">
                    <template v-if="me?.plan === 'standard'">スタンダードプラン</template>
                    <template v-else>フリープラン</template>
                  </div>
                </div>
                <div v-if="me?.plan === 'standard' && me?.plan_expiry" class="box grid grid-cols-[150px_1fr]">
                  <div class="head">プラン有効期限</div>
                  <div class="text">{{ me.plan_expiry }}</div>
                </div>
                <div class="box grid grid-cols_[150px_1fr]">
                  <div class="head">プラスプロフィール</div>
                  <div class="text">{{ me?.option_expiry ? 'オプション購入済み' : 'オプション未購入' }}</div>
                </div>
                <div v-if="me?.option_expiry" class="box grid grid-cols-[150px_1fr]">
                  <div class="head">オプション有効期限</div>
                  <div class="text">{{ me.option_expiry }}</div>
                </div>
              </div>
            </div>
          </li>
          <li><router-link to="/footprints"><IconPaw />あしあと</router-link></li>
          <li><router-link to="/likes/sent"><IconHeart />いいね</router-link></li>
          <li><router-link to="/chats"><IconMail />メッセージ</router-link></li>
          <li><router-link :to="{name: 'plan-checkout'}"><IconConfetti />プラン購入</router-link></li>
          <li><router-link to="/contact"><IconProgressHelp />お問い合わせ</router-link></li>
        </ul>
      </section>
    </template>
  </div>
</template>


<style lang="scss">

  .first-area{
    .col-4{
      .area{

        .numb{
          height: 62px;
          flex-shrink: 0;  // 縮まないように固定
        }

      }
    }
  }

  .tab-nav{
    button{
      border: none;
      background: transparent;
      padding: 10px 6px 6px;
      flex: 1;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      font-weight: 700;
      color: #555;
      position: relative;
      transition: color 0.2s ease;

      &::after{
        content: '';
        position: absolute;
        left: 10%;
        right: 10%;
        bottom: 0;
        height: 2px;
        background: #111;
        opacity: 0.08;
        transform: scaleX(0);
        transform-origin: center;
        transition: transform 0.2s ease, opacity 0.2s ease;
      }

      &.active{
        color: #111;

        &::after{
          opacity: 1;
          transform: scaleX(1);
        }
      }

      .badge{
        background: rgba(0,0,0,0.06);
        color: inherit;
        padding: 2px 8px;
        border-radius: 999px;
        font-size: 0.8rem;
      }
    }
  }

  .recos {
    .reco-scroll {
      scrollbar-width: none;
      &::-webkit-scrollbar { display: none; }
    }
    .reco-card {
      min-width: 90px;
    }
  }

  .profile-feed-mini{
      margin-bottom: 8px;
      .media--avatar{
          display: flex;
          align-items: center;
          justify-content: center;
      }
  }

</style>
