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

import 'flatpickr/dist/flatpickr.min.css'

// tabler
import { IconMapPin, IconHeart, IconLocation, IconSearch, IconHome, IconMessages, IconMenu2, IconSend, IconClock, IconChevronRight, IconUpload,IconZoomCheck, IconBrandTinder, IconPaw, IconMail, IconConfetti, IconProgressHelp ,IconChevronDown } from '@tabler/icons-vue'

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
app.component('IconUpload', IconUpload)
app.component('IconZoomCheck', IconZoomCheck)
app.component('IconBrandTinder', IconBrandTinder)
app.component('IconPaw', IconPaw)
app.component('IconMail', IconMail)
app.component('IconConfetti', IconConfetti)
app.component('IconProgressHelp', IconProgressHelp)
app.component('IconChevronDown', IconChevronDown)

app.component('Avatar', Avatar) // ← <Avatar> をどこでも使えるように
app.mount('#app')