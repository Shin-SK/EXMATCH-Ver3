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
      <section class="checklist mb-0">
        <ProfileChecklist />
      </section>
      <section class="profile" v-if="me">
        <div class="d-flex w-100 align-items-center justify-content-between my-4">
          <div class="name-area">
            <div class="fw-bold fs-1">{{ me.nickname || me.username }}</div>
            <div class="d-flex"><IconMapPin :size="16" />{{ me.area || me.main_area || '未設定' }}</div>
          </div>
          <div class="avatar-area">
            <Avatar :src="$avatar.me(me)" :size="80" :to="href" />
          </div>
        </div>
        <div class="d-flex justify-content-between align-items-center" style="border-bottom: 1px gray solid;">
        <div class="fw-bold fs-3 me-2">LCIQスコア</div>
        <router-link :to="{ name:'h2lciq' }" class="text-muted d-block mt-2 fs-5">スコアをあげるには？</router-link>          
        </div>

        <div class="lciq-box d-flex justify-content-between align-items-center mb-4">
          <div class="box">
            <div class="fw-bold p-2" style="font-size: 4rem;">{{ me.lciq_score ?? me.lciq ?? '-' }}</div>
          </div>
          <div class="wrap">
            <div class="d-flex align-items-center jusify-content-center gap-2">
              <router-link class="btn btn-warning d-flex align-items-center" :to="{ name:'h2lciq' }">再診断</router-link>
              <router-link class="btn btn-primary d-flex align-items-center" :to="{ name:'profile-edit' }">編集<i class="bi bi-chevron-right"></i></router-link>            
            </div>
            
          </div>
        </div>

      </section>

      <section class="score mb-4">
        <div class="score__wrap">
          <div class="box like">
            <div class="title"><i class="fas fa-heart"></i>いいね</div>
            <div class="numb">{{ likeCount }}</div>
            <router-link class="btn btn-primary"  :to="{ name:'liked' }">確認する</router-link>
          </div>
          <div class="box prof">
            <div class="title">プロフ充実度</div>
            <div class="numb">{{ completeness.percent }}</div>
            <router-link class="btn btn-primary" :to="{ name:'profile-edit' }">編集する</router-link>
            <div class="point">{{ completeness.answered }} / {{ completeness.total }} 項目回答済み</div>
          </div>
        </div>
      </section>

<section class="matched">
  <div class="head-title">マッチしたユーザー</div>
  <div class="area">
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
  </div>
</section>

      <!-- 置換: likesTop の描画 -->
<section class="followed" id="followed">
  <div class="head-title">いいねしてくれたユーザー</div>
  <div class="area">
      <template v-if="likesTop.length" class="feed feed-mini">
        <UserCardMini
          v-for="like in likesTop"
          :key="like.id"
          :user="like.from_user"
          :created-at="like.created_at"
          :link-to="`/users/${like.from_user?.id}`"
        />
      </template>
      <div v-else class="d-flex justify-content-center align-items-center w-100" style="height: 20vh;">
        <router-link to="/users">出会いはすぐそこに</router-link>
      </div>
    </div>
    <p class="more text-center">
      <router-link to="/likes/received">一覧を見る<i class="fas fa-angle-right"></i></router-link>
    </p>
</section>

      <!-- 折りたたみ①: プロフィール詳細 -->
      <section class="add-profile">
        <button
          class="fw-bold d-flex align-items-center justify-content-center m-auto gap-1"
          data-bs-toggle="collapse"
          data-bs-target="#profile-area"
          aria-expanded="false"
          aria-controls="profile-area">
          あなたのプロフィール<IconChevronRight />
        </button>
        <div class="collapse wrap" id="profile-area">
          <div class="area">
            <div class="box">
              <div class="head">自己紹介</div>
              <div class="text">{{ me?.bio || '未設定' }}</div>
            </div>
          </div>
        </div>
      </section>

      <!-- 折りたたみ②: 契約情報 -->
      <section class="user-info">
        <button
          class="fw-bold d-flex align-items-center justify-content-center m-auto gap-1"
          data-bs-toggle="collapse"
          data-bs-target="#user-area"
          aria-expanded="false"
          aria-controls="user-area">
          ユーザー情報<IconChevronRight />
        </button>
        <div id="user-area" class="area collapse">
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
      </section>

      <section class="menu">
        <ul>
          <li><router-link to="/footprints"><span class="material-symbols-outlined">barefoot</span>あしあと</router-link></li>
          <li><router-link to="/likes/sent"><span class="material-symbols-outlined">favorite</span>いいね</router-link></li>
          <li><router-link to="/chats"><span class="material-symbols-outlined">forum</span>メッセージ</router-link></li>
          <li><router-link :to="{name: 'plan-checkout'}"><span class="material-symbols-outlined">stat_3</span>プラン購入</router-link></li>
          <li><router-link to="/contact"><span class="material-symbols-outlined">help_center</span>お問い合わせ</router-link></li>
        </ul>
      </section>
    </template>
  </div>
</template>
