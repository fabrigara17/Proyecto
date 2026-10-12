<script setup>
import { onMounted, ref } from 'vue'
import { getCursosAsignados } from '@/services/asistencias'
import { mensajeError } from '@/utils/errores'
import AppIcon from '@/components/AppIcon.vue'

const cursos = ref([])
const cargando = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    cursos.value = await getCursosAsignados()
  } catch (e) {
    error.value = mensajeError(e, 'No pudimos cargar tus cursos. Probá de nuevo en un momento.')
  } finally {
    cargando.value = false
  }
})
</script>

<template>
  <div class="pagina">
    <h1 class="titulo-pagina">Asistencias</h1>
    <p class="mt-1 text-sm text-slate-500">Elegí un curso para pasar lista.</p>

    <p v-if="cargando" class="mt-6 text-slate-500">Cargando...</p>
    <p v-else-if="error" role="alert" class="mt-6 rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-600">
      {{ error }}
    </p>
    <p
      v-else-if="!cursos.length"
      class="mt-6 rounded-xl bg-amber-50 p-3 text-sm font-semibold text-amber-700"
    >
      No tenés cursos asignados todavía. Pedile al administrador que te asigne uno.
    </p>

    <ul v-else class="mt-5 grid gap-3 md:grid-cols-2 lg:grid-cols-3">
      <li v-for="c in cursos" :key="c.id">
        <router-link
          :to="{ name: 'asistencia-curso', params: { cursoId: c.id } }"
          class="flex items-center gap-4 rounded-2xl border border-blue-100 bg-white p-4 shadow-sm transition hover:border-brand"
        >
          <span class="grid size-12 shrink-0 place-items-center rounded-xl bg-blue-50 text-brand">
            <AppIcon name="check" class="size-6" />
          </span>
          <span class="min-w-0 flex-1">
            <span class="block truncate font-bold text-slate-900">{{ c.nombre }}</span>
            <span class="block text-xs text-slate-500">Año lectivo {{ c.anio_lectivo }}</span>
          </span>
          <AppIcon name="arrow-right" class="size-5 shrink-0 text-slate-400" />
        </router-link>
      </li>
    </ul>
  </div>
</template>