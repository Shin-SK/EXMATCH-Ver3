// src/router.js
import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '@/stores/useAuth'
import { useUser } from '@/stores/useUser'

const routes = [
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    children: [
      { path: '', redirect: '/mypage' },
      { path: 'mypage',     name: 'mypage',     component: () => import('@/views/MyPage.vue'),   meta:{ title:'MyPage' } },
      { path: 'search',      name: 'search',     component: () => import('@/views/Search.vue'), meta:{ title:'Search' } },
      { path: 'users/:uid', name: 'user-detail', component: () => import('@/views/UserProfileDetail.vue'), meta:{ title:'User' }, props:true },
      { path: 'matches', component: () => import('@/views/Matches.vue'), meta: { title: 'Matches' } },
      { path: 'chats',      name: 'chats',      component: () => import('@/views/Chats.vue'),    meta:{ title:'Chats' } },
      { path: 'chats/:uid', name: 'chat-room',  component: () => import('@/views/ChatRoom.vue'), meta:{ title:'Chat' }, props:true },
      { path: 'likes/received',name: 'liked', component: () => import('@/views/LikesReceived.vue'), meta: { title: 'Likes Received' } },
      { path: '/likes/sent', component: () => import('@/views/LikesSent.vue'), meta: { title: 'Likes Sent' } },
      { path: 'footprints', component: () => import('@/views/Footprints.vue'), meta: { title: 'Footprints' } },
      { path: 'profile/edit', name: 'profile-edit', component: () => import('@/views/ProfileEdit.vue'), meta: { title: 'プロフィール編集' } },
      { path: 'contact', name: 'contact', component: () => import('@/views/Contact.vue'), meta:{ title:'お問い合わせ', requiresAuth:false } },
      { path: 'h2lciq', name: 'h2lciq', component: () => import('@/views/H2Lciq.vue'), meta:{ title:'LCIQスコアはどうやってはかるの？', requiresAuth: false, skipOnboarding: true }},
      { path: 'plan/checkout', name: 'plan-checkout', component: () => import('@/views/PlanCheckout.vue'), meta:{ title:'プラン購入' } },
      { path: 'plan/success', name: 'plan-success', component: () => import('@/views/PlanSuccess.vue'), meta:{ title:'決済完了' } },
      { path: 'signup', name: 'signup', component: () => import('@/views/Signup.vue'), meta:{ title:'新規登録', requiresAuth:false } },
      { path: 'onboarding', name: 'onboarding', component: () => import('@/views/Onboarding.vue'),meta:{ title:'初期設定', requiresAuth:true } },

    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/home'},
  { path: '/login', name: 'login', component: () => import('@/views/Login.vue'), meta:{ title:'Login', requiresAuth:false } },
  { path: '/home', name: 'home', component: () => import('@/views/Home.vue'), meta:{ title:'Home', requiresAuth:false } },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(){ return { top: 0 } },
})

router.afterEach((to) => {
  if (to.meta?.title) document.title = to.meta.title
})



// src/router.js （beforeEach を一部差し替え）
router.beforeEach(async (to) => {
  const auth = useAuth()
  if (!auth.token) auth.initFromStorage()

  if (to.path === '/') {
    return auth.isAuthed ? { path: '/mypage' } : { path: '/home' }
  }
  const need = to.meta?.requiresAuth !== false
  if (need && !auth.isAuthed) {
    return { path: '/home', query: { next: to.fullPath } }
  }
  if (to.path === '/login' && auth.isAuthed) {
    return { path: '/mypage' }
  }

  // ★ここでスキップ判定
  const skipOnboarding = to.meta?.skipOnboarding === true

  if (auth.isAuthed && !skipOnboarding) {
    const user = useUser()
    try {
      if (!user.me) await user.fetchMe()
      const incomplete = user.me && user.me.is_profile_complete === false
      if (incomplete && to.path !== '/onboarding') {
        return { path: '/onboarding' }
      }
      if (!incomplete && to.path === '/onboarding') {
        return { path: '/mypage' }
      }
    } catch (_) {}
  }
})


export default router
