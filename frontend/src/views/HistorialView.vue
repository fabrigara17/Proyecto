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

// Estados de asistencia: etiqueta, color de la insignia y color del número del resumen
const ESTADOS = [
  { valor: 'PRESENTE', plural: 'Presentes', insignia: 'bg-green-100 text-green-700', numero: 'text-green-600' },
  { valor: 'AUSENTE', plural: 'Ausentes', insignia: 'bg-red-100 text-red-600', numero: 'text-red-500' },
  { valor: 'TARDE', plural: 'Llegadas tarde', insignia: 'bg-amber-100 text-amber-700', numero: 'text-amber-600' },
  { valor: 'RETIRO', plural: 'Retiros anticipados', insignia: 'bg-blue-100 text-blue-700', numero: 'text-blue-600' },
]
const ESTADO_POR_VALOR = Object.fromEntries(ESTADOS.map((e) => [e.valor, e]))

const asistencias = ref([])
const calificaciones = ref([])
const cargando = ref(true)
const error = ref('')

// Si es familia, se muestran solo los datos del alumno elegido en los chips
const filtrar = (lista) =>
  alumnos.seleccionadoId ? lista.filter((i) => i.alumno === alumnos.seleccionadoId) : lista

const asistenciasVisibles = computed(() => filtrar(asistencias.value))
const calificacionesVisibles = computed(() => filtrar(calificaciones.value))
const resumen = computed(() =>
  ESTADOS.map((e) => ({
    ...e,
    cantidad: asistenciasVisibles.value.filter((a) => a.estado === e.valor).length,
  })),
)

// Docentes, preceptores y admin ven varios alumnos: mostramos el nombre en cada fila
const mostrarAlumno = computed(() => !alumnos.seleccionadoId)

// ---- Calificaciones agrupadas por materia y etapa ----
const promedio = (lista) => lista.reduce((suma, n) => suma + Number(n), 0) / lista.length
const porFecha = (a, b) => a.fecha.localeCompare(b.fecha) || a.id - b.id

const notasAgrupadas = computed(() => {
  const mapa = new Map()
  for (const c of calificacionesVisibles.value) {
    const clave = `${c.alumno}|${c.materia}`
    if (!mapa.has(clave)) {
      mapa.set(clave, { clave, materia: c.materia_nombre, alumno: c.alumno_nombre, etapas: new Map() })
    }
    const etapas = mapa.get(clave).etapas
    const nombreEtapa = c.etapa_nombre ?? 'Sin etapa'
    if (!etapas.has(nombreEtapa)) etapas.set(nombreEtapa, [])
    etapas.get(nombreEtapa).push(c)
  }

  return [...mapa.values()]
    .map((g) => {
      const etapas = [...g.etapas]
        .map(([nombre, notas]) => {
          const ordenadas = [...notas].sort(porFecha)
          return { nombre, notas: ordenadas, promedio: promedio(ordenadas.map((n) => n.nota)) }
        })
        .sort((a, b) => a.notas[0].fecha.localeCompare(b.notas[0].fecha))
      return {
        clave: g.clave,
        materia: g.materia,
        alumno: g.alumno,
        etapas,
        // Promedio de la materia: el promedio de los promedios de cada etapa
        promedio: promedio(etapas.map((e) => e.promedio)),
      }
    })
    .sort((a, b) => a.materia.localeCompare(b.materia) || a.alumno.localeCompare(b.alumno))
})

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
      <div class="mt-4 grid grid-cols-2 gap-3 md:max-w-2xl md:grid-cols-4">
        <div
          v-for="r in resumen"
          :key="r.valor"
          class="rounded-2xl bg-white p-3 text-center shadow-sm ring-1 ring-slate-100"
        >
          <p class="text-2xl font-extrabold" :class="r.numero">{{ r.cantidad }}</p>
          <p class="text-xs font-semibold text-slate-500">{{ r.plural }}</p>
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
              <template v-if="mostrarAlumno">{{ a.alumno_nombre }} · </template>
              {{ a.materia_nombre || a.curso_nombre }}
              <template v-if="a.hora_inicio"> · {{ a.hora_inicio }} a {{ a.hora_fin }} hs</template>
            </p>
          </div>
          <span
            class="shrink-0 rounded-full px-3 py-1 text-xs font-bold"
            :class="ESTADO_POR_VALOR[a.estado]?.insignia"
          >
            {{ a.estado_display }}
          </span>
        </li>
      </ul>
    </template>

    <!-- Calificaciones: por materia y por etapa -->
    <template v-else>
      <p v-if="!notasAgrupadas.length" class="mt-6 text-slate-500">No hay calificaciones cargadas todavía.</p>
      <ul v-else class="mt-4 grid items-start gap-3 md:grid-cols-2">
        <li
          v-for="g in notasAgrupadas"
          :key="g.clave"
          class="rounded-2xl border border-blue-100 bg-white p-4 shadow-sm"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <p class="truncate font-bold text-slate-900">{{ g.materia }}</p>
              <p v-if="mostrarAlumno" class="truncate text-sm text-slate-500">{{ g.alumno }}</p>
            </div>
            <div class="shrink-0 text-right">
              <p class="text-[11px] font-bold uppercase tracking-wide text-slate-400">Promedio</p>
              <p class="text-xl font-extrabold text-brand">{{ formatoNota(g.promedio) }}</p>
            </div>
          </div>

          <div v-for="e in g.etapas" :key="e.nombre" class="mt-3 border-t border-slate-100 pt-2">
            <div class="flex items-center justify-between gap-2">
              <p class="text-sm font-bold text-slate-700">{{ e.nombre }}</p>
              <p class="text-xs font-semibold text-slate-500">Promedio {{ formatoNota(e.promedio) }}</p>
            </div>
            <ul class="mt-1.5 flex flex-wrap gap-2">
              <li
                v-for="n in e.notas"
                :key="n.id"
                class="rounded-xl bg-blue-50 px-2.5 py-1.5 text-center"
                :title="fechaCorta(n.fecha)"
              >
                <span class="block text-base font-extrabold text-brand">{{ formatoNota(n.nota) }}</span>
                <span class="block text-[10px] font-semibold text-slate-500">{{ n.detalle || fechaCorta(n.fecha) }}</span>
              </li>
            </ul>
          </div>
        </li>
      </ul>
    </template>
  </div>
</template>