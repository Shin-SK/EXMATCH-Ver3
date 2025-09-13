<script setup>
import { watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/api'
import { useAuth } from '@/stores/useAuth'
import SlideOver from '@/components/SlideOver.vue'

const props = defineProps({ modelValue: { type:Boolean, default:false } })
const emit  = defineEmits(['update:modelValue'])

const route = useRoute()
const router = useRouter()
const auth = useAuth()

const open = computed({
	get: () => props.modelValue,
	set: v  => emit('update:modelValue', v)
})

watch(() => route.fullPath, () => { open.value = false })

async function doLogout() {
	try { await api.post('auth/logout/') } catch {}
	try { localStorage.removeItem('token') } catch {}
	if (api?.defaults?.headers?.common) delete api.defaults.headers.common.Authorization
	try { auth.token = ''; auth.user = null } catch {}
	open.value = false
	router.replace('/home')
}
</script>

<template>
	<SlideOver v-model="open" side="left" width="80vw" title="">
		<div class="d-flex flex-column justify-content-between gap-2 pt-2" style="min-height:100%;">
			<div class="wrap d-flex flex-column gap-4">
				<router-link to="/mypage">マイページ<IconChevronRight :size="16" /></router-link>
				<router-link to="/search">検索<IconChevronRight :size="16" /></router-link>
				<router-link to="/chats">メッセージ<IconChevronRight :size="16" /></router-link>
				<router-link to="/profile/edit">設定<IconChevronRight :size="16" /></router-link>
			</div>

			<div class="mt-auto" style="text-align:center; color: lightgray;">
				<button type="button" class="btn btn-outline-danger w-100" @click="doLogout">ログアウト</button>
			</div>
		</div>
	</SlideOver>
</template>

<style scoped lang="scss">
.wrap a{
	border-bottom: 1px dotted lightgray;
	display:flex; justify-content:space-between; align-items:center;
	padding:10px 0;
}
</style>
