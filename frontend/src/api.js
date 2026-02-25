// src/api.js
import axios from 'axios'
import { router } from '@/router'

const BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000/api/'
if (!/\/api\/?$/.test(BASE)) console.warn('[api] VITE_API_BASE は /api/ で終わらせてください:', BASE)

export const api = axios.create({ baseURL: BASE })  // ← withCredentials等は使わない



api.interceptors.request.use(cfg => {
  const t = localStorage.getItem('token')
  cfg.headers = cfg.headers || {}
  if (t) cfg.headers.Authorization = `Token ${t}`
  return cfg
})

// 期限切れでログイン画面へ

let _authKickInProgress = false

api.interceptors.response.use(
  r => r,
  err => {
    const st = err?.response?.status
    if (st === 401) {
      // 失効・不正トークンは即破棄
      localStorage.removeItem('token')
      delete api.defaults.headers.common.Authorization

      // 今いる場所を next に積んでログインへ
      const here = window.location.pathname + window.location.search
      if (window.location.pathname !== '/login') {
        window.location.assign(`/login?next=${encodeURIComponent(here)}`)
      }
    }
    return Promise.reject(err)
  }
)


/* ───────── API wrappers ───────── */
export const fetchMe              = () => api.get('me/').then(r => r.data)
export const fetchMatches         = (page=1) => api.get('matches/',        { params:{ page } }).then(r => r.data)
export const fetchLikesReceived   = (page=1) => api.get('likes/received/', { params:{ page } }).then(r => r.data)
export const fetchProfileFields   = () => api.get('profile-fields/').then(r => r.data)
export const fetchMyCustomFields  = () => api.get('me/custom-fields/').then(r => r.data)
export const fetchChats           = (page=1) => api.get('chats/', { params:{ page } }).then(r => r.data)

export const fetchMessages = (userId, after=0) => api
  .get(`chats/${userId}/messages/`, { params:{ after } })
  .then(r => Array.isArray(r.data) ? r.data : (r.data.items || r.data.results || []))

export const fetchUnread          = () => api.get('notifications/unread/').then(r => r.data)


export const listify = (d) => Array.isArray(d) ? d : (d?.results || d?.items || d?.data || []);

export const fetchChatThreads = () =>
  api.get('chats/').then(res => listify(res.data));

export const sendMessage = (userId, body) =>
  api.post(`chats/${userId}/messages/`, { text: body })   // ← text に修正
    .then(r => r.data)
    .catch(err => {
      const data = err.response?.data || {};
      if (err.response?.status === 403 && data.detail_code) {
        throw new Error(`${data.detail} [${data.detail_code}]`);
      }
      throw err;
    });

export const markAllNotificationsRead = () =>
  api.post('notifications/read-all/').then(r => r.data).catch(() => ({}));

export const fetchChatUnreadMap = () =>
  api.get('chats/unread-map/').then(r => r.data)

export const readChatThread = (userId) =>
  api.post(`chats/${userId}/read/`).then(r => r.data)

export const likeUser = (userId) =>
  api.post('like/', { user_id: Number(userId) }).then(r => r.data)

export const unmatchUser = (userId) =>
  api.post(`unmatch/${Number(userId)}/`).then(r => r.data)


export const fetchFootprints = (page=1) =>
  api.get('footprints/', { params:{ page } }).then(r => r.data)

export const fetchLikesSent = (page=1) =>
  api.get('likes/sent/', { params:{ page } }).then(r => r.data)


export const fetchProfile = (userId) =>
  api.get(`profiles/${Number(userId)}/`).then(r => r.data)

export const toggleBlock = (userId) =>
  api.post(`block/${Number(userId)}/toggle/`).then(r => r.data)

export const createReport = (reported_id, reason, comment='', anonymous=false) =>
  api.post('reports/', { reported_id: Number(reported_id), reason, comment, anonymous }).then(r => r.data)

export const touchFootprint = (userId) =>
  api.post(`footprints/${Number(userId)}/touch/`).then(r => r.data)

export const fetchProfiles = (params = {}, page = 1) =>
  api.get('profiles/', { params: { ...params, page } }).then(r => r.data)


// === 既存の下あたりに追記 ===

// 固定プロフィール更新
export const updateMe = (payload) =>
  api.patch('me/', payload).then(r => r.data)

// カスタム項目（動的フィールド）更新
export const updateMyCustomFields = (values) =>
  api.patch('me/custom-fields/', values).then(r => r.data)

// アバター
export const uploadAvatar = (file) => {
  const fd = new FormData()
  fd.append('image', file)
  return api.post('me/avatar/', fd, { headers:{ 'Content-Type':'multipart/form-data' }})
           .then(r => r.data)
}
export const deleteAvatar = () =>
  api.delete('me/avatar/').then(r => r.data)

// 本人確認（提出一覧・提出・削除）
export const listVerifications = (params={}) =>
  api.get('verifications/', { params }).then(r => r.data)

export const uploadVerification = (docType, file) => {
  const fd = new FormData()
  fd.append('doc_type', docType)
  fd.append('image', file)
  return api.post('verifications/', fd, { headers:{ 'Content-Type':'multipart/form-data' }})
           .then(r => r.data)
}
export const deleteVerification = (pk) =>
  api.delete(`verifications/${pk}/`).then(r => r.data)


// ---- 決済（未実装なら後でURLを合わせて差し替え）----
export const createCheckout = (payload) =>
  api.post('payments/checkout/', payload).then(r => r.data)

export const sendContact = (payload) =>
  api.post('contact/', payload).then(r => r.data)


export const register = ({ username, email, password1, password2 }) =>
  api.post('auth/registration/', { username, email, password1, password2 })
     .then(r => r.data)


export const fetchRecommendations = () =>
  api.get('recommendations/').then(r => r.data?.items ?? [])

/* ── 開発用: 健全性チェック ── */
export function __apiCheck() {
  const tests = [
    ['me',               fetchMe()],
    ['matches',          fetchMatches(1)],
    ['likes/received',   fetchLikesReceived(1)],
    ['profile-fields',   fetchProfileFields()],
    ['me/custom-fields', fetchMyCustomFields()],
  ].map(([name, p]) =>
    p.then(() => ({ name, ok:true }))
     .catch(e => ({ name, ok:false, status:e?.response?.status, data:e?.response?.data }))
  )
  return Promise.all(tests).then(rows => { console.table(rows); return rows })
}

if (import.meta.env.DEV) {
  window.__apiCheck = __apiCheck
}
