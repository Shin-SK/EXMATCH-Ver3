<!-- src/views/MyPage.vue -->
<script setup>
import { ref, onMounted } from 'vue'
import {
  fetchMe, fetchMatches, fetchLikesReceived,
  fetchProfileFields, fetchMyCustomFields
} from '@/api'
import { useProfiles } from '@/stores/useProfiles'
import { useAuth } from '@/stores/useAuth'
import Avatar from '@/components/Avatar.vue'
import UserCardMini from '@/components/UserCardMini.vue'
import UserCard from '@/components/UserCard.vue'
import ProfileChecklist from '@/components/ProfileChecklist.vue'
import { uniqById } from '@/utils/uniq'
import { IconChevronRight, IconMapPin, IconHeart, IconPencil } from '@tabler/icons-vue'

const me = ref(null)
const matched = ref([])
const likesTop = ref([])
const likeCount = ref(0)
const completeness = ref({ percent: 0, answered: 0, total: 0 })
const loading = ref(true)
const err = ref('')
const activeTab = ref('matched')  // navタブの選択状態
const href = { name: 'profile-edit' }  // Avatarリンク先
const profiles = useProfiles()

const auth = useAuth()
const doLogout = async () => { await auth.logout(); location.href = '/login' }

onMounted(async () => {
  loading.value = true
  try {
    const [meData, mData, lData, fields, custom] = await Promise.all([
      fetchMe(),
      fetchMatches(1),
      fetchLikesReceived(1),
      fetchProfileFields(),
      fetchMyCustomFields(),
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

    // --- プロフ充実度 ---
    const reqKeys  = fieldsArr.filter(f => f.required).map(f => f.field_key)
    const answered = reqKeys.filter(k => !!customObj[k]).length
    const total    = reqKeys.length || 1
    completeness.value = { percent: Math.round((answered/total)*100), answered, total }
  } catch (e) {
    err.value = '読み込みに失敗しました'
    console.error('[MyPage]', e?.response?.status, e?.response?.data || e)
  } finally {
    loading.value = false
  }
})


</script>

<template>
  <div id="mypage" class="mypage">
    <div v-if="loading">Loading...</div>
    <div v-else-if="err">{{ err }}</div>

    <template v-else>
      <section class="profile pt-5" v-if="me">
        <div class="df-center flex-column my-5">
          <div class="avatar-area">
            <Avatar :src="$avatar.me(me)" :size="120" :to="href" />
          </div>
          <div class="name-area text-center">
            <div class="fw-bold">{{ me.nickname || me.username }}</div>
            <div class="df-center"><IconMapPin :size="16" />{{ me.area || me.main_area || '未設定' }}</div>
          </div>

        </div>
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
          <IconHeart />いいね
          <span v-if="likeCount" class="badge">{{ likeCount }}</span>
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
            <template v-if="likesTop.length" class="feed feed-mini">
              <UserCardMini
                v-for="like in likesTop"
                :key="like.id"
                :user="like.from_user"
                :created-at="like.created_at"
                :link-to="`/users/${like.from_user?.id}`"
              />
              <p class="more text-center">
                <router-link to="/likes/received">一覧を見る<i class="fas fa-angle-right"></i></router-link>
              </p>
            </template>
            <div v-else class="d-flex justify-content-center align-items-center w-100" style="height: 20vh;">
              <router-link to="/users">出会いはすぐそこに</router-link>
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



</style>