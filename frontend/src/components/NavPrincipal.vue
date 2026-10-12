<script setup>
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import AppIcon from '@/components/AppIcon.vue'

const auth = useAuthStore()

const ITEMS = [
  { to: '/', texto: 'Inicio', icono: 'home', exacto: true },
  { to: '/comunicados', texto: 'Comunicados', icono: 'bell' },
  { to: '/historial', texto: 'Historial', icono: 'clock' },
  { to: '/notificaciones', texto: 'Avisos', icono: 'chat' },
  { to: '/perfil', texto: 'Perfil', icono: 'user' },
  { to: '/materiales', texto: 'Materiales', icono: 'document' },
]

const ASISTENCIAS = { to: '/asistencias', texto: 'Asistencias', icono: 'check' }

const ITEMS_ADMIN = [
  { to: '/', texto: 'Inicio', icono: 'home', exacto: true },
  { to: '/comunicados', texto: 'Comunicados', icono: 'bell' },
  { to: '/usuarios', texto: 'Usuarios', icono: 'user-plus' },
  { to: '/cursos', texto: 'Cursos', icono: 'academic-cap' },
  { to: '/materias', texto: 'Materias', icono: 'book-open' },
  { to: '/familias', texto: 'Familias', icono: 'users' },
  { to: '/perfil', texto: 'Perfil', icono: 'user' },
]

const items = computed(() => {
  if (auth.rol === 'ADMIN') return ITEMS_ADMIN
  // El preceptor no tiene Historial: en su lugar tiene Asistencias
  if (auth.rol === 'PRECEPTOR') {
    return ITEMS.map((item) => (item.to === '/historial' ? ASISTENCIAS : item))
  }
  return ITEMS
})
</script>

<template>
  <!-- Celular: barra inferior -->
  <nav class="fixed inset-x-0 bottom-0 z-20 border-t border-slate-200 bg-white pb-[env(safe-area-inset-bottom)] md:hidden">
    <ul class="mx-auto flex max-w-lg justify-around px-2 pt-2 pb-1.5">
      <li v-for="item in items" :key="item.to">
        <router-link :to="item.to" custom v-slot="{ href, navigate, isActive, isExactActive }">
          <a
            :href="href"
            @click="navigate"
            class="flex min-w-14 flex-col items-center gap-0.5 px-1 text-[11px] font-semibold"
            :class="(item.exacto ? isExactActive : isActive) ? 'text-brand' : 'text-slate-400'"
          >
            <AppIcon :name="item.icono" class="size-6" />
            {{ item.texto }}
          </a>
        </router-link>
      </li>
    </ul>
  </nav>

  <!-- Computadora: barra lateral -->
  <aside class="sticky top-0 hidden h-dvh w-64 shrink-0 flex-col border-r border-slate-200 bg-white p-4 md:flex">
    <div class="mb-6 flex items-center gap-3 px-2 pt-2">
      <span class="grid size-10 place-items-center rounded-xl bg-brand text-white">
        <AppIcon name="chat" class="size-6" />
      </span>
      <span class="text-xl font-extrabold text-brand-dark">Libreta Digital</span>
    </div>

    <nav class="flex flex-col gap-1">
      <router-link
        v-for="item in items"
        :key="item.to"
        :to="item.to"
        custom
        v-slot="{ href, navigate, isActive, isExactActive }"
      >
        <a
          :href="href"
          @click="navigate"
          class="flex items-center gap-3 rounded-xl px-3 py-2.5 font-semibold transition"
          :class="(item.exacto ? isExactActive : isActive) ? 'bg-blue-50 text-brand' : 'text-slate-500 hover:bg-slate-50'"
        >
          <AppIcon :name="item.icono" class="size-5" />
          {{ item.texto }}
        </a>
      </router-link>
    </nav>
  </aside>
</template>