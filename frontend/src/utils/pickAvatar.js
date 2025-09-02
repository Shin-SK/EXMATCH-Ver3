// src/utils/pickAvatar.js
// ① 名前付きヘルパー
export function pickAvatar(obj = {}) {
  const cand = [
    obj.profile_image_url,
    obj.profile_image,
    obj.avatar_url,
    obj.user?.profile_image_url,
    obj.partner_avatar,
    obj.partner?.avatar_url,
  ].find(Boolean)
  return typeof cand === 'string' ? cand : ''
}

export const pickMe   = (me = {}) => pickAvatar(me)
export const pickUser = (u  = {}) => pickAvatar(u)

// ② プラグイン（$avatar で使えるように）
export default {
  install(app) {
    app.config.globalProperties.$avatar = {
      pick: pickAvatar,
      me:   pickMe,
      user: pickUser,
    }
  }
}
