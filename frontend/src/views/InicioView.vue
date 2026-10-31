<script setup>
import { computed, onMounted, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useAlumnosStore } from '@/stores/alumnos'
import { getCantidadNoLeidas } from '@/services/notificaciones'
import { nombreCompleto } from '@/utils/formato'
import AppIcon from '@/components/AppIcon.vue'
import CalendarioMensual from '@/components/CalendarioMensual.vue'

const auth = useAuthStore()
const alumnos = useAlumnosStore()

const sinLeer = ref(0)
const error = ref('')

const nombre = computed(() => nombreCompleto(auth.usuario))
const rol = computed(() => auth.usuario?.rol_display ?? '')
const curso = computed(() => auth.usuario?.curso ?? null)

onMounted(async () => {
  try {
    const [cantidad] = await Promise.all([
      getCantidadNoLeidas(),
      alumnos.cargar(auth.rol),
    ])
    sinLeer.value = cantidad
  } catch {
    error.value = 'No pudimos cargar la información. Probá de nuevo en un momento.'
  }
})
</script>

<template>
  <div class="pagina">
    <header class="flex items-start justify-between gap-3">
      <div class="min-w-0">
        <h1 class="titulo-pagina">{{ nombre }}</h1>
        <p class="mt-1.5 flex flex-wrap items-center gap-2 text-sm text-slate-500">
          <span>{{ rol }}</span>
          <span
            v-if="curso"
            class="rounded-md border border-slate-200 bg-white px-2 py-0.5 text-xs font-medium text-slate-600"
          >
            Curso {{ curso }}
          </span>
        </p>
      </div>

      <router-link
        to="/notificaciones"
        aria-label="Avisos"
        class="relative grid size-10 shrink-0 place-items-center rounded-md border border-slate-200 bg-white text-slate-500 transition-colors hover:border-slate-300 hover:bg-slate-50 hover:text-brand"
      >
        <AppIcon name="bell" class="size-5" />
        <span
          v-if="sinLeer > 0"
          class="absolute top-2 right-2 size-2 rounded-full bg-red-500 ring-2 ring-white"
        ></span>
      </router-link>
    </header>

    <p v-if="error" class="mt-4 rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-600">{{ error }}</p>

    <router-link
      to="/notificaciones"
      class="group mt-5 flex items-center gap-4 rounded-lg border border-slate-200 border-l-4 border-l-brand bg-white p-4 transition-colors hover:bg-slate-50 md:p-5"
    >
      <span class="min-w-8 text-3xl font-semibold tabular-nums text-brand-dark">{{ sinLeer }}</span>
      <span class="flex-1">
        <span class="block font-semibold text-slate-900">Avisos sin leer</span>
        <span class="block text-sm text-slate-500">Ver avisos nuevos</span>
      </span>
      <AppIcon
        name="arrow-right"
        class="size-5 shrink-0 text-slate-400 transition duration-150 group-hover:translate-x-0.5 group-hover:text-brand"
      />
    </router-link>

    <section class="mt-6">
      <h2 class="mb-3 text-lg font-semibold text-slate-900">Calendario</h2>
      <CalendarioMensual />
    </section>
  </div>
</template>