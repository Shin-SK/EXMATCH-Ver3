// src/main.js
import { createApp } from 'vue'
import App from './App.vue'
import { router } from './router'

import { api } from '@/api'
const t = localStorage.getItem('token')
if (t) api.defaults.headers.common.Authorization = `Token ${t}`

import { registerSW } from 'virtual:pwa-register'
registerSW({ immediate: true })

import { createPinia } from 'pinia'


import Avatar from '@/components/Avatar.vue'
import pickAvatar from '@/utils/pickAvatar'

// tabler
import { IconMapPin, IconHeart, IconLocation, IconSearch, IconHome, IconMessages, IconMenu2, IconSend, IconClock, IconChevronRight } from '@tabler/icons-vue'

import '@/styles/bootstrap.scss'  
import 'bootstrap/dist/js/bootstrap.bundle.min.js'
import '@/styles/main.scss' 


const app = createApp(App)
app.use(router)
app.use(pickAvatar)
app.use(createPinia())

//tabler
app.component('IconMapPin', IconMapPin)
app.component('IconHeart', IconHeart)
app.component('IconLocation', IconLocation)
app.component('IconSearch', IconSearch)
app.component('IconHome', IconHome)
app.component('IconMessages', IconMessages)
app.component('IconMenu2', IconMenu2)
app.component('IconSend', IconSend)
app.component('IconClock', IconClock)
app.component('IconChevronRight', IconChevronRight)

app.component('Avatar', Avatar) // ← <Avatar> をどこでも使えるように
app.mount('#app')