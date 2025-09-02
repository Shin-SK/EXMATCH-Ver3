// src/stores/useUser.js
import { defineStore } from 'pinia'
import { api } from '@/api'

export const useUser = defineStore('user', {
  state: () => ({
    me: null,
    loading: false,
    error: '',
  }),
  actions: {
    async fetchMe() {
      this.loading = true
      this.error = ''
      try {
        const { data } = await api.get('me/')
        this.me = data
      } catch (e) {
        this.error = e?.response?.data?.detail || '読み込みに失敗しました'
        throw e
      } finally {
        this.loading = false
      }
    },
    async patchMe(payload) {
      const { data } = await api.patch('me/', payload)
      this.me = data
    },
    clear() { this.me = null; this.error = '' },
  },
})
