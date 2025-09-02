// src/stores/useAuth.js
import { defineStore } from 'pinia'
import { api } from '@/api'
const KEY = 'token'

export const useAuth = defineStore('auth', {
  state: () => ({ token: localStorage.getItem(KEY) || '' }),
  getters: { isAuthed: s => !!s.token },
  actions: {
    setToken(t){ this.token = t || ''; if(t){ localStorage.setItem(KEY,t); api.defaults.headers.common.Authorization=`Token ${t}` } else { localStorage.removeItem(KEY); delete api.defaults.headers.common.Authorization } },
    async login(username, password){
      const { data } = await api.post('auth/login/', { username, password })
      this.setToken(data.key)
    },
    async logout(){ try{ await api.post('auth/logout/') }catch{} this.setToken('') },
    initFromStorage(){ const t = localStorage.getItem(KEY); if(t) this.setToken(t) }
  }
})
