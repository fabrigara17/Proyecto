<script setup>
import { computed, onMounted, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useAlumnosStore } from '@/stores/alumnos'
import { getComunicacionesRecientes } from '@/services/comunicaciones'
import { getCantidadNoLeidas } from '@/services/notificaciones'
import { nombreCompleto } from '@/utils/formato'
import AppIcon from '@/components/AppIcon.vue'
import ChipsAlumnos from '@/components/ChipsAlumnos.vue'
import ComunicadoCard from '@/components/ComunicadoCard.vue'

const auth = useAuthStore()
const alumnos = useAlumnosStore()

const recientes = ref([])
const sinLeer = ref(0)
const cargando = ref(true)
const error = ref('')

const nombre = computed(() => auth.usuario?.first_name || auth.usuario?.username)

onMounted(async () => {
  try {
    const [coms, cantidad] = await Promise.all([
      getComunicacionesRecientes(3),
      getCantidadNoLeidas(),
      alumnos.cargar(auth.rol),
    ])
    recientes.value = coms
    sinLeer.value = cantidad
  } catch {
    error.value = 'No pudimos cargar la información. Probá de nuevo en un momento.'
  } finally {
    cargando.value = false
  }
})
</script>

<template>
  <div class="pagina">
    <header class="flex items-start justify-between gap-3">
      <div>
        <h1 class="titulo-pagina">Hola, {{ nombre }} 👋</h1>
        <p v-if="alumnos.seleccionado" class="text-sm text-slate-500">
          Alumno:
          <span class="font-semibold text-brand">{{ nombreCompleto(alumnos.seleccionado) }}</span>
        </p>
      </div>

      <router-link
        to="/notificaciones"
        aria-label="Avisos"
        class="relative grid size-11 shrink-0 place-items-center rounded-full bg-white text-slate-500 shadow-sm ring-1 ring-slate-100 hover:text-brand"
      >
        <AppIcon name="bell" class="size-6" />
        <span
          v-if="sinLeer > 0"
          class="absolute top-2.5 right-2.5 size-2.5 rounded-full bg-red-500 ring-2 ring-white"
        ></span>
      </router-link>
    </header>

    <ChipsAlumnos class="mt-3" />

    <router-link
      to="/notificaciones"
      class="mt-5 flex items-center gap-4 rounded-2xl bg-linear-to-br from-brand to-brand-dark p-4 text-white shadow-lg shadow-brand/25 md:p-6"
    >
      <span class="grid size-12 place-items-center rounded-xl bg-white/20 text-2xl font-extrabold">
        {{ sinLeer }}
      </span>
      <span class="flex-1">
        <span class="block font-bold md:text-lg">Avisos sin leer</span>
        <span class="block text-sm text-white/80">Tocá para ver los nuevos avisos</span>
      </span>
      <span class="grid size-9 place-items-center rounded-lg bg-white/20">
        <AppIcon name="arrow-right" class="size-5" />
      </span>
    </router-link>

    <section class="mt-6">
      <div class="flex items-center justify-between">
        <h2 class="text-lg font-extrabold text-slate-900">Recientes</h2>
        <router-link to="/comunicados" class="text-sm font-bold text-brand">Ver todos</router-link>
      </div>

      <p v-if="cargando" class="mt-4 text-slate-500">Cargando...</p>
      <p v-else-if="error" class="mt-4 rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-600">{{ error }}</p>
      <p v-else-if="!recientes.length" class="mt-4 text-slate-500">Todavía no hay comunicados.</p>
      <div v-else class="mt-3 grid gap-3 md:grid-cols-2 lg:grid-cols-3">
        <ComunicadoCard v-for="c in recientes" :key="c.id" :comunicado="c" />
      </div>
    </section>
  </div>
</template>