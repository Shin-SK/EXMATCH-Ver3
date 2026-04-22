// src/stores/useUnread.js（置換）
import { defineStore } from 'pinia'
import { fetchChatUnreadMap, readChatThread } from '@/api'

let t = null

export const useUnread = defineStore('unread', {
  state: () => ({
    count: 0,           // 全チャット未読合計
    map  : {},          // { sender_id: 未読数 }
    polling: false,
    _refreshing: false, // refresh 同時実行ガード
    lastFetchedAt: 0,
  }),
  actions: {
    async refresh(){
      if (this._refreshing) return
      this._refreshing = true
      try{
        const d = await fetchChatUnreadMap()
        this.count = d?.count | 0
        this.map   = d?.by_sender || {}
        this.lastFetchedAt = Date.now()
      }catch{}
      finally{
        this._refreshing = false
      }
    },
    startPolling(ms=8000){
      if (this.polling) return
      this.polling = true
      this.refresh()
      t = setInterval(() => this.refresh(), ms)
    },
    stopPolling(){
      if (t){ clearInterval(t); t=null }
      this.polling = false
    },
    async readThread(userId){
      try{
        await readChatThread(userId)
      }catch(e){
        console.error('[useUnread] readThread failed', e)
        return
      }
      const n = this.map?.[userId] || 0
      if (n){
        this.count = Math.max(0, this.count - n)
        this.map   = { ...this.map, [userId]: 0 }
      }
    },
    of(userId){ return this.map?.[userId] || 0 },
  }
})
