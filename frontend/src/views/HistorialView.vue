<script setup>
import { computed, onMounted, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useAlumnosStore } from '@/stores/alumnos'
import { getAsistencias } from '@/services/asistencias'
import { getCalificaciones } from '@/services/calificaciones'
import { fechaCorta, fechaLarga, formatoNota } from '@/utils/formato'
import ChipsAlumnos from '@/components/ChipsAlumnos.vue'

const auth = useAuthStore()
const alumnos = useAlumnosStore()

const secciones = [
  { id: 'asistencias', texto: 'Asistencias' },
  { id: 'calificaciones', texto: 'Calificaciones' },
]
const seccion = ref('asistencias')

const asistencias = ref([])
const calificaciones = ref([])
const cargando = ref(true)
const error = ref('')

// Si es familia, se muestran solo los datos del alumno elegido en los chips
const filtrar = (lista) =>
  alumnos.seleccionadoId ? lista.filter((i) => i.alumno === alumnos.seleccionadoId) : lista

const asistenciasVisibles = computed(() => filtrar(asistencias.value))
const calificacionesVisibles = computed(() => filtrar(calificaciones.value))
const presentes = computed(() => asistenciasVisibles.value.filter((a) => a.presente).length)
const ausentes = computed(() => asistenciasVisibles.value.length - presentes.value)

// Docentes, preceptores y admin ven varios alumnos: mostramos el nombre en cada fila
const mostrarAlumno = computed(() => !alumnos.seleccionadoId)

onMounted(async () => {
  try {
    const [a, c] = await Promise.all([
      getAsistencias(),
      getCalificaciones(),
      alumnos.cargar(auth.rol),
    ])
    asistencias.value = a
    calificaciones.value = c
  } catch {
    error.value = 'No pudimos cargar el historial. Probá de nuevo en un momento.'
  } finally {
    cargando.value = false
  }
})
</script>

<template>
  <div class="pagina">
    <h1 class="titulo-pagina">Desempeño Académico</h1>

    <ChipsAlumnos class="mt-3" />

    <div class="mt-4 grid grid-cols-2 rounded-2xl bg-slate-200/70 p-1 md:max-w-sm">
      <button
        v-for="s in secciones"
        :key="s.id"
        type="button"
        @click="seccion = s.id"
        class="rounded-xl py-2 text-sm font-bold transition"
        :class="seccion === s.id ? 'bg-white text-brand shadow-sm' : 'text-slate-500'"
      >
        {{ s.texto }}
      </button>
    </div>

    <p v-if="cargando" class="mt-6 text-slate-500">Cargando...</p>
    <p v-else-if="error" class="mt-6 rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-600">{{ error }}</p>

    <!-- Asistencias -->
    <template v-else-if="seccion === 'asistencias'">
      <div class="mt-4 grid grid-cols-2 gap-3 md:max-w-sm">
        <div class="rounded-2xl bg-white p-3 text-center shadow-sm ring-1 ring-slate-100">
          <p class="text-2xl font-extrabold text-green-600">{{ presentes }}</p>
          <p class="text-xs font-semibold text-slate-500">Presentes</p>
        </div>
        <div class="rounded-2xl bg-white p-3 text-center shadow-sm ring-1 ring-slate-100">
          <p class="text-2xl font-extrabold text-red-500">{{ ausentes }}</p>
          <p class="text-xs font-semibold text-slate-500">Ausentes</p>
        </div>
      </div>

      <p v-if="!asistenciasVisibles.length" class="mt-6 text-slate-500">No hay asistencias registradas.</p>
      <ul v-else class="mt-4 grid gap-2 md:grid-cols-2">
        <li
          v-for="a in asistenciasVisibles"
          :key="a.id"
          class="flex items-center justify-between gap-3 rounded-2xl border border-blue-100 bg-white p-4 shadow-sm"
        >
          <div class="min-w-0">
            <p class="font-bold text-slate-900 capitalize">{{ fechaLarga(a.fecha) }}</p>
            <p class="truncate text-sm text-slate-500">
              <template v-if="mostrarAlumno">{{ a.alumno_nombre }} · </template>{{ a.curso_nombre }}
            </p>
          </div>
          <span
            class="shrink-0 rounded-full px-3 py-1 text-xs font-bold"
            :class="a.presente ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'"
          >
            {{ a.presente ? 'Presente' : 'Ausente' }}
          </span>
        </li>
      </ul>
    </template>

    <!-- Calificaciones -->
    <template v-else>
      <p v-if="!calificacionesVisibles.length" class="mt-6 text-slate-500">No hay calificaciones cargadas todavía.</p>
      <ul v-else class="mt-4 grid gap-2 md:grid-cols-2">
        <li
          v-for="c in calificacionesVisibles"
          :key="c.id"
          class="flex items-center justify-between gap-3 rounded-2xl border border-blue-100 bg-white p-4 shadow-sm"
        >
          <div class="min-w-0">
            <p class="truncate font-bold text-slate-900">{{ c.materia_nombre }}</p>
            <p class="truncate text-sm text-slate-500">
              <template v-if="mostrarAlumno">{{ c.alumno_nombre }} · </template>{{ fechaCorta(c.fecha) }}
            </p>
          </div>
          <span class="grid size-12 shrink-0 place-items-center rounded-xl bg-blue-50 text-lg font-extrabold text-brand">
            {{ formatoNota(c.nota) }}
          </span>
        </li>
      </ul>
    </template>
  </div>
</template>