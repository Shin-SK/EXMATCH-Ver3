<script setup>
import { computed, watch, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
	modelValue: { type: Boolean, default: false },
	side: { type: String, default: 'right' }, // 'right' | 'left'
	width: { type: String, default: 'min(92vw, 360px)' },
	title: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue'])

const open = computed({
	get: () => props.modelValue,
	set: v  => emit('update:modelValue', v)
})

function onKey(e){ if(e.key === 'Escape') open.value = false }
watch(open, v => { document.documentElement.style.overflow = v ? 'hidden' : '' })
onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => {
	window.removeEventListener('keydown', onKey)
	document.documentElement.style.overflow = ''
})
</script>

<template>
	<Teleport to="body">
		<Transition name="fade">
			<div v-if="open" class="so__overlay" @click="open=false" />
		</Transition>

		<Transition :name="props.side === 'left' ? 'slide-left' : 'slide-right'">
			<aside
				v-if="open"
				class="so__panel"
				role="dialog" aria-modal="true"
				:style="{ width: props.width, [props.side]: '0' }"
			>
				<header class="so__head" v-if="props.title">
					<strong>{{ props.title }}</strong>
					<button class="btn btn-sm btn-outline-secondary" @click="open=false" aria-label="閉じる">×</button>
				</header>
				<div class="so__body">
					<slot />
				</div>
			</aside>
		</Transition>
	</Teleport>
</template>

<style scoped>
.so__overlay{ position:fixed; inset:0; z-index:1050; background:rgba(0,0,0,.25); }
.so__panel{ position:fixed; top:0; z-index:1051; height:100%; background:#fff; box-shadow:0 0 24px rgba(0,0,0,.12); display:flex; flex-direction:column; }
.so__head{ display:flex; justify-content:space-between; align-items:center; padding:12px 16px; border-bottom:1px solid #eee; }
.so__body{ padding:12px 16px; overflow:auto; }

/* overlay */
.fade-enter-active, .fade-leave-active { transition: opacity .18s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

/* slide */
.slide-right-enter-active, .slide-right-leave-active,
.slide-left-enter-active, .slide-left-leave-active { transition: transform .28s cubic-bezier(.2,.8,.2,1); will-change: transform; }
.slide-right-enter-from, .slide-right-leave-to { transform: translateX(100%); }
.slide-left-enter-from,  .slide-left-leave-to  { transform: translateX(-100%); }

@media (prefers-reduced-motion: reduce){
	.fade-enter-active, .fade-leave-active,
	.slide-right-enter-active, .slide-right-leave-active,
	.slide-left-enter-active,  .slide-left-leave-active { transition: none; }
}
</style>
