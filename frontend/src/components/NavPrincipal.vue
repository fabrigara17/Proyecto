<script setup>
import { computed, onBeforeUnmount, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useMenuLateral } from '@/composables/menuLateral'
import AppIcon from '@/components/AppIcon.vue'
import logo from '@/assets/logo.png'

const auth = useAuthStore()
const route = useRoute()
const menu = useMenuLateral()

const INICIO = { to: '/', texto: 'Inicio', icono: 'home', exacto: true }
const COMUNICADOS = { to: '/comunicados', texto: 'Comunicados', icono: 'bell' }
const DESEMPENO = { to: '/historial', texto: 'Desempeño Académico', icono: 'clock' }
const AVISOS = { to: '/notificaciones', texto: 'Avisos', icono: 'chat' }
const PERFIL = { to: '/perfil', texto: 'Perfil', icono: 'user' }
const MATERIALES = { to: '/materiales', texto: 'Materiales', icono: 'document' }
const ASISTENCIAS = { to: '/asistencias', texto: 'Asistencias', icono: 'check' }
const HORARIOS = { to: '/horarios', texto: 'Horarios', icono: 'calendar' }
const NOTAS = { to: '/notas', texto: 'Cargar notas', icono: 'academic-cap' }
const ETAPAS = { to: '/etapas', texto: 'Etapas de notas', icono: 'calendar' }
const ALUMNOS = { to: '/alumnos', texto: 'Alumnos', icono: 'users' }
const CURSOS = { to: '/cursos', texto: 'Cursos', icono: 'academic-cap' }
const MATERIAS = { to: '/materias', texto: 'Materias', icono: 'book-open' }
const EQUIPO = { to: '/equipo', texto: 'Equipo', icono: 'users' }
const USUARIOS = { to: '/usuarios', texto: 'Usuarios', icono: 'user-plus' }
const CHAT = { to: '/chat', texto: 'Chat', icono: 'chat' }

const ITEMS_BASE = [INICIO, COMUNICADOS, DESEMPENO, CHAT, AVISOS, PERFIL, MATERIALES]
const ITEMS_DOCENTE = [INICIO, COMUNICADOS, ASISTENCIAS, NOTAS, DESEMPENO, CHAT, AVISOS, PERFIL, MATERIALES]
const ITEMS_PRECEPTOR = [INICIO, COMUNICADOS, ASISTENCIAS, HORARIOS, ALUMNOS, CHAT, AVISOS, PERFIL, MATERIALES]
const ITEMS_CONDUCCION = [INICIO, CURSOS, MATERIAS, EQUIPO, ETAPAS, COMUNICADOS, CHAT, PERFIL]
const ITEMS_ADMIN = [INICIO, CURSOS, MATERIAS, EQUIPO, ETAPAS, COMUNICADOS, CHAT, USUARIOS, PERFIL]

const items = computed(() => {
  if (auth.rol === 'ADMIN') return ITEMS_ADMIN
  if (auth.rol === 'CONDUCCION') return ITEMS_CONDUCCION
  if (auth.rol === 'PRECEPTOR') return ITEMS_PRECEPTOR
  if (auth.rol === 'DOCENTE') return ITEMS_DOCENTE
  return ITEMS_BASE
})

// Cierra el menú al navegar
watch(() => route.fullPath, () => menu.cerrar())

// Bloquea el scroll de la página mientras el menú está abierto
watch(menu.abierto, (v) => {
  document.body.style.overflow = v ? 'hidden' : ''
})

function alTeclear(e) {
  if (e.key === 'Escape') menu.cerrar()
}
onMounted(() => window.addEventListener('keydown', alTeclear))
onBeforeUnmount(() => {
  window.removeEventListener('keydown', alTeclear)
  document.body.style.overflow = ''
})
</script>

<template>
  <!-- Menú lateral (celular) -->
  <div class="md:hidden">
    <Transition
      enter-active-class="transition-opacity duration-200 ease-out"
      leave-active-class="transition-opacity duration-150 ease-in"
      enter-from-class="opacity-0"
      leave-to-class="opacity-0"
    >
      <div
        v-if="menu.abierto.value"
        class="fixed inset-0 z-30 bg-slate-900/40"
        aria-hidden="true"
        @click="menu.cerrar()"
      />
    </Transition>

    <Transition
      enter-active-class="transition-transform duration-250 ease-out"
      leave-active-class="transition-transform duration-200 ease-in"
      enter-from-class="-translate-x-full"
      leave-to-class="-translate-x-full"
    >
      <aside
        v-if="menu.abierto.value"
        id="menu-lateral"
        role="dialog"
        aria-label="Menú principal"
        class="fixed inset-y-0 left-0 z-40 flex w-72 max-w-[85vw] flex-col bg-white p-4 shadow-xl"
      >
        <div class="mb-4 flex items-center justify-between gap-2 border-b border-slate-200 px-2 pt-1 pb-4">
          <div class="flex min-w-0 items-center gap-2">
            <img :src="logo" alt="" class="size-8" />
            <span class="truncate text-lg font-semibold tracking-tight text-brand-dark">Libreta Digital</span>
          </div>
          <button
            type="button"
            @click="menu.cerrar()"
            aria-label="Cerrar menú"
            class="grid size-10 shrink-0 place-items-center rounded-md text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-800"
          >
            <AppIcon name="x-mark" class="size-6" />
          </button>
        </div>

        <nav class="flex-1 overflow-y-auto pb-[env(safe-area-inset-bottom)]">
          <ul class="flex flex-col gap-0.5">
            <li v-for="item in items" :key="item.to">
              <router-link :to="item.to" custom v-slot="{ href, navigate, isActive, isExactActive }">
                <a
                  :href="href"
                  @click="navigate"
                  class="group relative flex items-center gap-3 rounded-md px-3 py-3 font-medium transition-colors duration-150 before:absolute before:inset-y-2 before:left-0 before:w-0.5 before:origin-center before:rounded-full before:bg-brand before:transition-transform before:duration-200"
                  :class="(item.exacto ? isExactActive : isActive)
                    ? 'bg-blue-100 text-brand-dark before:scale-y-100'
                    : 'text-slate-600 before:scale-y-0 hover:bg-blue-50 hover:text-slate-900'"
                >
                  <AppIcon
                    :name="item.icono"
                    class="size-5 shrink-0 transition-colors duration-150"
                    :class="(item.exacto ? isExactActive : isActive) ? 'text-brand' : 'text-slate-400 group-hover:text-slate-600'"
                  />
                  <span class="truncate">{{ item.texto }}</span>
                </a>
              </router-link>
            </li>
          </ul>
        </nav>
      </aside>
    </Transition>
  </div>

  <!-- Sidebar fijo (escritorio) -->
  <aside class="sticky top-0 hidden h-dvh w-64 shrink-0 flex-col border-r border-slate-200 bg-white p-4 md:flex">
    <div class="mb-5 flex items-center gap-3 border-b border-slate-200 px-2 pt-2 pb-5">
      <span class="grid size-9 place-items-center rounded-md bg-brand text-white">
        <AppIcon name="chat" class="size-5" />
      </span>
      <span class="text-lg font-semibold tracking-tight text-brand-dark">Libreta Digital</span>
    </div>

    <nav class="flex flex-col gap-0.5">
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
          class="group relative flex items-center gap-3 rounded-md px-3 py-2 text-[15px] font-medium transition-colors duration-150 before:absolute before:inset-y-1.5 before:left-0 before:w-0.5 before:origin-center before:rounded-full before:bg-brand before:transition-transform before:duration-200"
          :class="(item.exacto ? isExactActive : isActive)
            ? 'bg-blue-100 text-brand-dark before:scale-y-100'
            : 'text-slate-600 before:scale-y-0 hover:bg-blue-50 hover:text-slate-900'"
        >
          <AppIcon
            :name="item.icono"
            class="size-5 shrink-0 transition-colors duration-150"
            :class="(item.exacto ? isExactActive : isActive) ? 'text-brand' : 'text-slate-400 group-hover:text-slate-600'"
          />
          {{ item.texto }}
        </a>
      </router-link>
    </nav>
  </aside>
</template>