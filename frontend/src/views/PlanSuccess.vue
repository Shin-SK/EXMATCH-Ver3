<!-- src/views/PlanSuccess.vue -->
<script setup>
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
const route = useRoute(); const router = useRouter()
onMounted(()=>{ console.log('session_id=', route.query.session_id) })
</script>
<template>
  <div class="container py-5 text-center">
    <div class="head-set">
      <h2>PLAN</h2>
      <h3>購入完了</h3>
    </div>
    <p class="h4 mb-3">決済が完了しました</p>
    <p>反映まで少し時間がかかることがあります。</p>
    <router-link class="btn btn-primary mt-3" :to="{name:'mypage'}">マイページへ</router-link>
  </div>
</template>
