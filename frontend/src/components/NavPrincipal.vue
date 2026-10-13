<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppIcon from '@/components/AppIcon.vue'

const auth = useAuthStore()
const route = useRoute()

const INICIO = { to: '/', texto: 'Inicio', icono: 'home', exacto: true }
const CALENDARIO = { to: '/calendario', texto: 'Calendario', icono: 'calendar' }
const COMUNICADOS = { to: '/comunicados', texto: 'Comunicados', icono: 'bell' }
const DESEMPENO = { to: '/historial', texto: 'Desempeño Académico', icono: 'clock' }
const AVISOS = { to: '/notificaciones', texto: 'Avisos', icono: 'chat' }
const PERFIL = { to: '/perfil', texto: 'Perfil', icono: 'user' }
const MATERIALES = { to: '/materiales', texto: 'Materiales', icono: 'document' }
const ASISTENCIAS = { to: '/asistencias', texto: 'Asistencias', icono: 'check' }
const ALUMNOS = { to: '/alumnos', texto: 'Alumnos', icono: 'users' }
const CURSOS = { to: '/cursos', texto: 'Cursos', icono: 'academic-cap' }
const MATERIAS = { to: '/materias', texto: 'Materias', icono: 'book-open' }
const EQUIPO = { to: '/equipo', texto: 'Equipo', icono: 'users' }
const USUARIOS = { to: '/usuarios', texto: 'Usuarios', icono: 'user-plus' }

// Familia, alumno y docente
const ITEMS_BASE = [INICIO, CALENDARIO, COMUNICADOS, DESEMPENO, AVISOS, PERFIL, MATERIALES]
const ITEMS_PRECEPTOR = [INICIO, CALENDARIO, COMUNICADOS, ASISTENCIAS, ALUMNOS, AVISOS, PERFIL, MATERIALES]
const ITEMS_CONDUCCION = [INICIO, CALENDARIO, CURSOS, MATERIAS, EQUIPO, COMUNICADOS, PERFIL]
// El rol de desarrollo: lo mismo que conducción, más Usuarios
const ITEMS_ADMIN = [INICIO, CALENDARIO, CURSOS, MATERIAS, EQUIPO, COMUNICADOS, USUARIOS, PERFIL]

const items = computed(() => {
  if (auth.rol === 'ADMIN') return ITEMS_ADMIN
  if (auth.rol === 'CONDUCCION') return ITEMS_CONDUCCION
  if (auth.rol === 'PRECEPTOR') return ITEMS_PRECEPTOR
  return ITEMS_BASE
})

// Celular: hasta 5 ítems entran en la barra; si hay más, 4 y un botón "Más"
const MAXIMO_EN_BARRA = 5
const visibles = computed(() => (items.value.length > MAXIMO_EN_BARRA ? items.value.slice(0, 4) : items.value))
const extra = computed(() => (items.value.length > MAXIMO_EN_BARRA ? items.value.slice(4) : []))

const masAbierto = ref(false)
watch(() => route.fullPath, () => (masAbierto.value = false))

function activo(item) {
  return item.exacto ? route.path === item.to : route.path.startsWith(item.to)
}
const extraActivo = computed(() => extra.value.some(activo))
</script>

<template>
  <!-- Celular: barra inferior -->
  <nav class="fixed inset-x-0 bottom-0 z-20 border-t border-slate-200 bg-white pb-[env(safe-area-inset-bottom)] md:hidden">
    <div v-if="masAbierto && extra.length" class="border-b border-slate-100 px-3 py-2">
      <ul class="mx-auto grid max-w-lg grid-cols-4 gap-1">
        <li v-for="item in extra" :key="item.to" class="min-w-0">
          <router-link :to="item.to" custom v-slot="{ href, navigate }">
            <a
              :href="href"
              @click="navigate"
              class="flex flex-col items-center gap-0.5 rounded-xl px-1 py-2 text-[10px] font-semibold"
              :class="activo(item) ? 'bg-blue-50 text-brand' : 'text-slate-500'"
            >
              <AppIcon :name="item.icono" class="size-6 shrink-0" />
              <span class="max-w-full truncate">{{ item.texto }}</span>
            </a>
          </router-link>
        </li>
      </ul>
    </div>

    <ul class="mx-auto flex max-w-lg justify-around px-1 pt-2 pb-1.5">
      <li v-for="item in visibles" :key="item.to" class="min-w-0 flex-1">
        <router-link :to="item.to" custom v-slot="{ href, navigate, isActive, isExactActive }">
          <a
            :href="href"
            @click="navigate"
            class="flex flex-col items-center gap-0.5 px-0.5 text-[10px] font-semibold"
            :class="(item.exacto ? isExactActive : isActive) ? 'text-brand' : 'text-slate-400'"
          >
            <AppIcon :name="item.icono" class="size-6 shrink-0" />
            <span class="max-w-full truncate">{{ item.texto }}</span>
          </a>
        </router-link>
      </li>
      <li v-if="extra.length" class="min-w-0 flex-1">
        <button
          type="button"
          @click="masAbierto = !masAbierto"
          class="flex w-full flex-col items-center gap-0.5 px-0.5 text-[10px] font-semibold"
          :class="masAbierto || extraActivo ? 'text-brand' : 'text-slate-400'"
        >
          <AppIcon name="ellipsis" class="size-6 shrink-0" />
          <span>Más</span>
        </button>
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