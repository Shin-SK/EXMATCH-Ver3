// src/stores/useProfiles.js
import { defineStore } from 'pinia'
import { fetchProfile } from '@/api'

export const useProfiles = defineStore('profiles', {
  state: () => ({
    byId: {},          // { [id]: ProfileSerializer shape }
    loading: {},       // { [id]: boolean }
  }),
  actions: {
    ingest(p){ if(p && p.id) this.byId[p.id] = { ...this.byId[p.id], ...p } },
    ingestList(list){ (list || []).forEach(p => this.ingest(p)) },

    async ensure(id){
      id = Number(id)
      if(!id) return null
      if(this.byId[id]) return this.byId[id]
      if(this.loading[id]) return null
      this.loading[id] = true
      try{
        const p = await fetchProfile(id)
        this.ingest(p)
        return p
      } finally {
        this.loading[id] = false
      }
    },

    get(id){ return this.byId[Number(id)] || null },
    getMany(ids){ return (ids || []).map(i => this.get(i)).filter(Boolean) },
    clear(){ this.byId = {}; this.loading = {} },
  }
})
