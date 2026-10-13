<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  agregarMateriasAlCurso, asignarDocente, asignarPreceptor, editarCurso, eliminarCurso,
  getDetalleCurso, getMaterias, getSeguimientoCurso, quitarDocente, quitarMateriaDelCurso,
  quitarPreceptor,
} from '@/services/academico'
import { getUsuarios } from '@/services/usuarios'
import { mensajeError } from '@/utils/errores'
import { nombreCompleto } from '@/utils/formato'
import {
  anioCursada, COLOR_TURNO, etiquetaMes, nombreTurno, porcentaje, TURNOS,
} from '@/utils/texto'
import AppIcon from '@/components/AppIcon.vue'

const route = useRoute()
const router = useRouter()
const cursoId = computed(() => Number(route.params.id))

const PESTANAS = [
  { valor: 'seguimiento', texto: 'Seguimiento' },
  { valor: 'organizacion', texto: 'Organización' },
]
const tab = ref('seguimiento')

const curso = ref(null) // detalle: { materias, preceptores, alumnos, ... }
const materias = ref([])
const docentes = ref([])
const preceptores = ref([])

const cargando = ref(true)
const errorCarga = ref('')
const error = ref('')
const exito = ref('')
const procesando = ref(false)

// Seguimiento: se carga aparte para que un error ahí no tire abajo el resto de la pantalla
const seg = ref(null)
const cargandoSeg = ref(true)
const errorSeg = ref('')

const editando = ref(false)
const formCurso = ref({ nombre: '', anio_cursada: '', anio_lectivo: '', turno: '' })
const docenteElegido = ref({}) // { [materiaCursoId]: docenteId }
const preceptorNuevo = ref('')
const agregandoMaterias = ref(false)
const materiasNuevas = ref([])

onMounted(async () => {
  try {
    const [detalle, mats, docs, pres] = await Promise.all([
      getDetalleCurso(cursoId.value),
      getMaterias(),
      getUsuarios({ rol: 'DOCENTE' }),
      getUsuarios({ rol: 'PRECEPTOR' }),
    ])
    curso.value = detalle
    materias.value = mats
    docentes.value = docs
    preceptores.value = pres
  } catch (e) {
    errorCarga.value =
      e.response?.status === 404
        ? 'No encontramos este curso.'
        : mensajeError(e, 'No pudimos cargar el curso. Probá de nuevo.')
  } finally {
    cargando.value = false
  }
  if (curso.value) cargarSeguimiento()
})

async function cargarSeguimiento() {
  cargandoSeg.value = true
  errorSeg.value = ''
  try {
    seg.value = await getSeguimientoCurso(cursoId.value)
  } catch (e) {
    errorSeg.value = mensajeError(e, 'No pudimos cargar el seguimiento del curso.')
  } finally {
    cargandoSeg.value = false
  }
}

// ---- Colores según el valor (verde / ámbar / rojo) ----
function colorBarra(n, alto, medio) {
  if (n === null || n === undefined) return 'bg-slate-300'
  if (n >= alto) return 'bg-green-500'
  if (n >= medio) return 'bg-amber-500'
  return 'bg-red-500'
}

function colorTexto(n, alto, medio) {
  if (n === null || n === undefined) return 'text-slate-400'
  if (n >= alto) return 'text-green-600'
  if (n >= medio) return 'text-amber-600'
  return 'text-red-600'
}

const maxNotas = computed(() => {
  const cantidades = seg.value?.estadisticas.distribucion_notas.map((d) => d.cantidad) ?? []
  return Math.max(1, ...cantidades)
})

function promedio(n) {
  return n === null || n === undefined ? '—' : n.toLocaleString('es-AR')
}

// Lo que todavía se puede agregar (lo que ya está en el curso no se ofrece)
const materiasDisponibles = computed(() => {
  const usadas = new Set(curso.value.materias.map((m) => m.materia))
  return materias.value.filter((m) => !usadas.has(m.id))
})
const preceptoresDisponibles = computed(() => {
  const usados = new Set(curso.value.preceptores.map((p) => p.preceptor))
  return preceptores.value.filter((p) => !usados.has(p.id))
})
function docentesDisponibles(mc) {
  const usados = new Set(mc.docentes.map((d) => d.docente))
  return docentes.value.filter((d) => !usados.has(d.id))
}

// Ejecuta una acción y recarga el detalle. Devuelve true si salió bien.
async function ejecutar(accion, ok = '') {
  procesando.value = true
  error.value = ''
  exito.value = ''
  try {
    await accion()
    curso.value = await getDetalleCurso(cursoId.value)
    if (ok) exito.value = ok
    return true
  } catch (e) {
    error.value = mensajeError(e, 'No se pudo completar la acción.')
    return false
  } finally {
    procesando.value = false
  }
}

// ---- Datos del curso ----
function abrirEdicion() {
  formCurso.value = {
    nombre: curso.value.nombre,
    anio_cursada: curso.value.anio_cursada ?? '',
    anio_lectivo: curso.value.anio_lectivo,
    turno: curso.value.turno ?? '',
  }
  editando.value = true
  error.value = ''
  exito.value = ''
}

async function guardarCurso() {
  const ok = await ejecutar(
    () => editarCurso(cursoId.value, {
      nombre: formCurso.value.nombre.trim(),
      anio_cursada: formCurso.value.anio_cursada ? Number(formCurso.value.anio_cursada) : null,
      anio_lectivo: Number(formCurso.value.anio_lectivo),
      turno: formCurso.value.turno,
    }),
    'Datos del curso actualizados.',
  )
  if (ok) editando.value = false
}

async function borrarCurso() {
  if (!window.confirm(`¿Eliminar el curso ${curso.value.nombre}? Se quitan también sus materias, docentes y preceptores asignados.`)) return
  procesando.value = true
  error.value = ''
  try {
    await eliminarCurso(cursoId.value)
    router.push({ name: 'cursos' })
  } catch (e) {
    error.value = mensajeError(e, 'No se pudo eliminar el curso.')
  } finally {
    procesando.value = false
  }
}

// ---- Preceptores ----
async function agregarPreceptor() {
  if (!preceptorNuevo.value) return
  const ok = await ejecutar(() => asignarPreceptor(cursoId.value, Number(preceptorNuevo.value)))
  if (ok) preceptorNuevo.value = ''
}

function quitarPreceptorDe(p) {
  return ejecutar(() => quitarPreceptor(p.id))
}

// ---- Materias (varias a la vez) ----
function alternarTodasNuevas() {
  const todas = materiasDisponibles.value.map((m) => m.id)
  materiasNuevas.value = materiasNuevas.value.length === todas.length ? [] : todas
}

async function agregarMaterias() {
  if (!materiasNuevas.value.length) return
  const ok = await ejecutar(() => agregarMateriasAlCurso(cursoId.value, materiasNuevas.value))
  if (ok) {
    materiasNuevas.value = []
    agregandoMaterias.value = false
  }
}

function quitarMateria(mc) {
  if (!window.confirm(`¿Quitar ${mc.materia_nombre} de este curso? También se quitan sus profesores asignados.`)) return
  return ejecutar(() => quitarMateriaDelCurso(mc.id))
}

// ---- Profesores de cada materia ----
async function asignarADocente(mc) {
  const docente = docenteElegido.value[mc.id]
  if (!docente) return
  const ok = await ejecutar(() => asignarDocente(mc.id, Number(docente)))
  if (ok) docenteElegido.value[mc.id] = ''
}

function quitarDocenteDe(d) {
  return ejecutar(() => quitarDocente(d.id))
}
</script>

<template>
  <div class="pagina">
    <router-link :to="{ name: 'cursos' }" class="inline-flex items-center gap-1 text-sm font-bold text-brand">
      <AppIcon name="arrow-right" class="size-4 rotate-180" />
      Cursos
    </router-link>

    <p v-if="cargando" class="mt-6 text-slate-500">Cargando...</p>
    <p v-else-if="errorCarga" role="alert" class="mt-6 rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-600">
      {{ errorCarga }}
    </p>

    <template v-else-if="curso">
      <!-- Encabezado -->
      <div class="mt-2 flex items-start justify-between gap-3">
        <div class="min-w-0">
          <div class="flex items-center gap-2">
            <h1 class="titulo-pagina truncate">{{ curso.nombre }}</h1>
            <span
              v-if="curso.turno"
              class="shrink-0 rounded-full px-2.5 py-0.5 text-xs font-bold"
              :class="COLOR_TURNO[curso.turno]"
            >
              {{ nombreTurno(curso.turno) }}
            </span>
          </div>
          <p class="text-sm text-slate-500">
            {{ anioCursada(curso.anio_cursada) }} · Año lectivo {{ curso.anio_lectivo }}
          </p>
          <p class="text-sm text-slate-500">
            Preceptor:
            <span class="font-semibold text-slate-700">
              {{ curso.preceptores.map((p) => p.preceptor_nombre).join(', ') || 'sin asignar' }}
            </span>
          </p>
        </div>
        <div v-if="!editando" class="flex shrink-0 gap-3 pt-1 text-sm font-bold">
          <button type="button" @click="abrirEdicion" class="text-brand">Editar</button>
          <button type="button" @click="borrarCurso" :disabled="procesando" class="text-red-600">Eliminar</button>
        </div>
      </div>

      <form
        v-if="editando"
        @submit.prevent="guardarCurso"
        class="mt-3 grid gap-3 rounded-2xl border border-blue-100 bg-white p-4 shadow-sm md:max-w-xl"
      >
        <label class="block">
          <span class="text-sm font-semibold text-slate-600">Nombre *</span>
          <input v-model="formCurso.nombre" required maxlength="50" class="campo" />
        </label>
        <div class="grid gap-3 sm:grid-cols-3">
          <label class="block">
            <span class="text-sm font-semibold text-slate-600">Año de cursada</span>
            <select v-model="formCurso.anio_cursada" class="campo">
              <option value="">Sin especificar</option>
              <option v-for="n in 7" :key="n" :value="n">{{ n }}º año</option>
            </select>
          </label>
          <label class="block">
            <span class="text-sm font-semibold text-slate-600">Turno</span>
            <select v-model="formCurso.turno" class="campo">
              <option value="">Sin turno</option>
              <option v-for="t in TURNOS" :key="t.valor" :value="t.valor">{{ t.texto }}</option>
            </select>
          </label>
          <label class="block">
            <span class="text-sm font-semibold text-slate-600">Año lectivo *</span>
            <input v-model="formCurso.anio_lectivo" required type="number" min="2000" max="2100" class="campo" />
          </label>
        </div>
        <div class="flex gap-3">
          <button type="submit" :disabled="procesando" class="boton-principal">Guardar</button>
          <button type="button" @click="editando = false" class="rounded-xl px-4 font-bold text-slate-500 hover:bg-slate-100">
            Cancelar
          </button>
        </div>
      </form>

      <p v-if="error" role="alert" class="mt-4 rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-600">
        {{ error }}
      </p>
      <p v-if="exito" role="status" class="mt-4 rounded-xl bg-green-50 p-3 text-sm font-semibold text-green-700">
        {{ exito }}
      </p>

      <!-- Pestañas -->
      <div class="mt-5 flex gap-1 rounded-2xl bg-slate-200/60 p-1 md:max-w-md">
        <button
          v-for="t in PESTANAS"
          :key="t.valor"
          type="button"
          @click="tab = t.valor"
          class="flex-1 rounded-xl px-3 py-2 text-sm font-bold transition"
          :class="tab === t.valor ? 'bg-white text-brand shadow-sm' : 'text-slate-500'"
        >
          {{ t.texto }}
        </button>
      </div>

      <!-- ================= SEGUIMIENTO ================= -->
      <template v-if="tab === 'seguimiento'">
        <p v-if="cargandoSeg" class="mt-6 text-slate-500">Cargando seguimiento...</p>
        <p v-else-if="errorSeg" role="alert" class="mt-6 rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-600">
          {{ errorSeg }}
        </p>

        <div v-else-if="seg" class="mt-5 grid items-start gap-5 lg:grid-cols-3">
          <!-- Asistencias -->
          <section class="rounded-2xl border border-blue-100 bg-white p-4 shadow-sm">
            <h2 class="font-bold text-slate-900">Asistencias</h2>

            <p class="mt-3 text-4xl font-extrabold" :class="colorTexto(seg.asistencia.porcentaje, 85, 75)">
              {{ porcentaje(seg.asistencia.porcentaje) }}
            </p>
            <p class="text-xs text-slate-500">
              de asistencia · {{ seg.asistencia.dias_registrados }}
              {{ seg.asistencia.dias_registrados === 1 ? 'clase registrada' : 'clases registradas' }}
            </p>

            <div class="mt-3 grid grid-cols-2 gap-2 text-center">
              <div class="rounded-xl bg-green-50 p-2">
                <p class="text-xl font-extrabold text-green-600">{{ seg.asistencia.presentes }}</p>
                <p class="text-xs font-semibold text-slate-500">Presentes</p>
              </div>
              <div class="rounded-xl bg-red-50 p-2">
                <p class="text-xl font-extrabold text-red-500">{{ seg.asistencia.ausentes }}</p>
                <p class="text-xs font-semibold text-slate-500">Ausentes</p>
              </div>
            </div>

            <h3 class="mt-4 text-sm font-bold text-slate-700">Por alumno</h3>
            <p class="text-xs text-slate-400">De menor a mayor asistencia</p>

            <p v-if="!seg.asistencia.por_alumno.length" class="mt-2 text-sm text-slate-500">
              El curso no tiene alumnos.
            </p>
            <ul v-else class="mt-1 max-h-96 divide-y divide-slate-100 overflow-y-auto">
              <li v-for="a in seg.asistencia.por_alumno" :key="a.alumno" class="py-2">
                <div class="flex items-center justify-between gap-2 text-sm">
                  <span class="min-w-0 truncate font-semibold text-slate-900">{{ a.alumno_nombre }}</span>
                  <span class="shrink-0 font-bold" :class="colorTexto(a.porcentaje, 85, 75)">
                    {{ porcentaje(a.porcentaje) }}
                  </span>
                </div>
                <div class="mt-1 h-1.5 rounded-full bg-slate-100">
                  <div
                    class="h-1.5 rounded-full"
                    :class="colorBarra(a.porcentaje, 85, 75)"
                    :style="{ width: (a.porcentaje ?? 0) + '%' }"
                  ></div>
                </div>
                <p class="mt-0.5 text-xs text-slate-400">
                  <template v-if="a.porcentaje === null">Sin registros</template>
                  <template v-else>
                    {{ a.ausentes }} {{ a.ausentes === 1 ? 'falta' : 'faltas' }} · {{ a.presentes }} presentes
                  </template>
                </p>
              </li>
            </ul>
          </section>

          <!-- Aprobación -->
          <section class="rounded-2xl border border-blue-100 bg-white p-4 shadow-sm">
            <h2 class="font-bold text-slate-900">Aprobación</h2>
            <p class="text-xs text-slate-500">
              Aprueba quien tiene promedio de {{ seg.aprobacion.nota_minima }} o más en la materia.
            </p>

            <p v-if="!seg.aprobacion.por_materia.length" class="mt-3 text-sm text-slate-500">
              El curso todavía no tiene materias.
            </p>
            <ul v-else class="mt-2 divide-y divide-slate-100">
              <li v-for="m in seg.aprobacion.por_materia" :key="m.materia" class="py-2">
                <div class="flex items-center justify-between gap-2 text-sm">
                  <span class="min-w-0 truncate font-semibold text-slate-900">{{ m.materia_nombre }}</span>
                  <span class="shrink-0 font-bold" :class="colorTexto(m.porcentaje_aprobacion, 70, 50)">
                    {{ porcentaje(m.porcentaje_aprobacion) }}
                  </span>
                </div>
                <div class="mt-1 h-1.5 rounded-full bg-slate-100">
                  <div
                    class="h-1.5 rounded-full"
                    :class="colorBarra(m.porcentaje_aprobacion, 70, 50)"
                    :style="{ width: (m.porcentaje_aprobacion ?? 0) + '%' }"
                  ></div>
                </div>
                <p class="mt-0.5 text-xs text-slate-400">
                  <template v-if="m.evaluados">
                    {{ m.aprobados }} de {{ m.evaluados }} aprueban · promedio {{ promedio(m.promedio) }}
                  </template>
                  <template v-else>Sin notas cargadas</template>
                </p>
              </li>
            </ul>

            <h3 class="mt-4 text-sm font-bold text-slate-700">Alumnos con materias desaprobadas</h3>
            <p v-if="!seg.aprobacion.alumnos_en_riesgo.length" class="mt-1 text-sm text-slate-500">
              Ninguno por ahora.
            </p>
            <ul v-else class="mt-1 max-h-64 divide-y divide-slate-100 overflow-y-auto">
              <li v-for="a in seg.aprobacion.alumnos_en_riesgo" :key="a.alumno" class="flex items-center justify-between gap-2 py-1.5 text-sm">
                <span class="min-w-0 truncate font-semibold text-slate-900">{{ a.alumno_nombre }}</span>
                <span class="shrink-0 rounded-full bg-red-50 px-2 py-0.5 text-xs font-bold text-red-600">
                  {{ a.materias_desaprobadas }}
                  {{ a.materias_desaprobadas === 1 ? 'materia' : 'materias' }}
                </span>
              </li>
            </ul>
          </section>

          <!-- Estadísticas -->
          <section class="rounded-2xl border border-blue-100 bg-white p-4 shadow-sm">
            <h2 class="font-bold text-slate-900">Estadísticas</h2>

            <div class="mt-3 grid grid-cols-2 gap-2 text-center">
              <div class="rounded-xl bg-slate-50 p-2">
                <p class="text-xl font-extrabold text-slate-900">{{ seg.estadisticas.total_alumnos }}</p>
                <p class="text-xs font-semibold text-slate-500">Alumnos</p>
              </div>
              <div class="rounded-xl bg-slate-50 p-2">
                <p class="text-xl font-extrabold text-slate-900">{{ seg.estadisticas.total_materias }}</p>
                <p class="text-xs font-semibold text-slate-500">Materias</p>
              </div>
              <div class="rounded-xl bg-slate-50 p-2">
                <p class="text-xl font-extrabold text-slate-900">{{ promedio(seg.estadisticas.promedio_general) }}</p>
                <p class="text-xs font-semibold text-slate-500">Promedio general</p>
              </div>
              <div class="rounded-xl bg-slate-50 p-2">
                <p class="text-xl font-extrabold text-slate-900">{{ seg.asistencia.dias_registrados }}</p>
                <p class="text-xs font-semibold text-slate-500">Clases registradas</p>
              </div>
            </div>

            <h3 class="mt-4 text-sm font-bold text-slate-700">Asistencia por mes</h3>
            <p v-if="!seg.estadisticas.asistencia_por_mes.length" class="mt-1 text-sm text-slate-500">
              Todavía no hay asistencias registradas.
            </p>
            <ul v-else class="mt-2 grid gap-2">
              <li v-for="m in seg.estadisticas.asistencia_por_mes" :key="m.mes">
                <div class="flex items-center justify-between text-xs">
                  <span class="font-semibold capitalize text-slate-600">{{ etiquetaMes(m.mes) }}</span>
                  <span class="font-bold" :class="colorTexto(m.porcentaje, 85, 75)">{{ porcentaje(m.porcentaje) }}</span>
                </div>
                <div class="mt-0.5 h-2 rounded-full bg-slate-100">
                  <div
                    class="h-2 rounded-full"
                    :class="colorBarra(m.porcentaje, 85, 75)"
                    :style="{ width: (m.porcentaje ?? 0) + '%' }"
                  ></div>
                </div>
              </li>
            </ul>

            <h3 class="mt-4 text-sm font-bold text-slate-700">Distribución de notas</h3>
            <ul class="mt-2 grid gap-2">
              <li v-for="d in seg.estadisticas.distribucion_notas" :key="d.rango">
                <div class="flex items-center justify-between text-xs">
                  <span class="font-semibold text-slate-600">{{ d.rango }}</span>
                  <span class="font-bold text-slate-700">{{ d.cantidad }}</span>
                </div>
                <div class="mt-0.5 h-2 rounded-full bg-slate-100">
                  <div
                    class="h-2 rounded-full bg-brand"
                    :style="{ width: (d.cantidad * 100 / maxNotas) + '%' }"
                  ></div>
                </div>
              </li>
            </ul>
          </section>
        </div>
      </template>

      <!-- ================= ORGANIZACIÓN ================= -->
      <template v-else>
        <!-- Preceptor -->
        <section class="mt-5 rounded-2xl border border-blue-100 bg-white p-4 shadow-sm">
          <h2 class="font-bold text-slate-900">Preceptor</h2>

          <div class="mt-2 flex flex-wrap gap-1.5">
            <span
              v-for="p in curso.preceptores"
              :key="p.id"
              class="inline-flex items-center gap-1 rounded-full bg-blue-50 py-1 pl-3 pr-1.5 text-sm font-bold text-brand"
            >
              {{ p.preceptor_nombre }}
              <button
                type="button"
                @click="quitarPreceptorDe(p)"
                :disabled="procesando"
                aria-label="Quitar preceptor"
                class="grid size-5 place-items-center rounded-full hover:bg-blue-100"
              >
                <AppIcon name="x-mark" class="size-3.5" />
              </button>
            </span>
            <span v-if="!curso.preceptores.length" class="text-sm font-semibold text-amber-600">
              Sin preceptor asignado
            </span>
          </div>

          <div class="mt-3 flex gap-2 md:max-w-md">
            <select v-model="preceptorNuevo" class="campo">
              <option value="">Asignar preceptor...</option>
              <option v-for="p in preceptoresDisponibles" :key="p.id" :value="p.id">{{ nombreCompleto(p) }}</option>
            </select>
            <button
              type="button"
              @click="agregarPreceptor"
              :disabled="procesando || !preceptorNuevo"
              class="shrink-0 rounded-xl bg-brand px-4 text-sm font-bold text-white disabled:opacity-50"
            >
              Asignar
            </button>
          </div>
        </section>

        <div class="mt-5 grid items-start gap-5 lg:grid-cols-2">
          <!-- Materias y profesores -->
          <section class="rounded-2xl border border-blue-100 bg-white p-4 shadow-sm">
            <div class="flex items-center justify-between gap-2">
              <h2 class="font-bold text-slate-900">Materias ({{ curso.materias.length }})</h2>
              <button
                v-if="!agregandoMaterias"
                type="button"
                @click="agregandoMaterias = true"
                class="text-sm font-bold text-brand"
              >
                Agregar materias
              </button>
            </div>

            <!-- Agregar varias materias a la vez -->
            <div v-if="agregandoMaterias" class="mt-3 grid gap-2 rounded-xl border border-slate-200 p-3">
              <p v-if="!materiasDisponibles.length" class="text-sm text-slate-500">
                No quedan materias para agregar. Podés crear más en la pestaña Materias.
              </p>
              <template v-else>
                <label class="flex items-center gap-2 text-sm font-bold text-brand">
                  <input
                    type="checkbox"
                    :checked="materiasNuevas.length === materiasDisponibles.length"
                    @change="alternarTodasNuevas"
                    class="size-4"
                  />
                  Seleccionar todas ({{ materiasDisponibles.length }})
                </label>
                <div class="grid max-h-48 gap-1 overflow-y-auto">
                  <label v-for="m in materiasDisponibles" :key="m.id" class="flex items-center gap-2 text-sm text-slate-800">
                    <input type="checkbox" :value="m.id" v-model="materiasNuevas" class="size-4" />
                    {{ m.nombre }}
                  </label>
                </div>
              </template>
              <div class="flex gap-3">
                <button
                  type="button"
                  @click="agregarMaterias"
                  :disabled="procesando || !materiasNuevas.length"
                  class="rounded-xl bg-brand px-4 py-2 text-sm font-bold text-white disabled:opacity-50"
                >
                  Agregar ({{ materiasNuevas.length }})
                </button>
                <button
                  type="button"
                  @click="agregandoMaterias = false; materiasNuevas = []"
                  class="text-sm font-bold text-slate-500"
                >
                  Cancelar
                </button>
              </div>
            </div>

            <p v-if="!curso.materias.length" class="mt-3 text-sm text-slate-500">Este curso todavía no tiene materias.</p>

            <ul v-else class="mt-3 grid gap-3">
              <li v-for="mc in curso.materias" :key="mc.id" class="rounded-xl border border-slate-100 p-3">
                <div class="flex items-center justify-between gap-2">
                  <p class="min-w-0 truncate font-bold text-slate-900">{{ mc.materia_nombre }}</p>
                  <button
                    type="button"
                    @click="quitarMateria(mc)"
                    :disabled="procesando"
                    aria-label="Quitar materia del curso"
                    class="shrink-0 text-slate-400 hover:text-red-600"
                  >
                    <AppIcon name="x-mark" class="size-5" />
                  </button>
                </div>

                <!-- Profesores de la materia -->
                <ul class="mt-1.5 grid gap-1">
                  <li v-for="d in mc.docentes" :key="d.id" class="flex items-center justify-between gap-2 text-sm text-slate-700">
                    <span class="min-w-0 truncate">{{ d.docente_nombre }}</span>
                    <button
                      type="button"
                      @click="quitarDocenteDe(d)"
                      :disabled="procesando"
                      aria-label="Quitar profesor"
                      class="shrink-0 text-slate-300 hover:text-red-600"
                    >
                      <AppIcon name="x-mark" class="size-4" />
                    </button>
                  </li>
                  <li v-if="!mc.docentes.length" class="text-sm font-semibold text-amber-600">Sin profesor asignado</li>
                </ul>

                <div class="mt-2 flex gap-2">
                  <select
                    :value="docenteElegido[mc.id] ?? ''"
                    @change="docenteElegido[mc.id] = $event.target.value"
                    class="campo"
                  >
                    <option value="">Asignar profesor...</option>
                    <option v-for="d in docentesDisponibles(mc)" :key="d.id" :value="d.id">{{ nombreCompleto(d) }}</option>
                  </select>
                  <button
                    type="button"
                    @click="asignarADocente(mc)"
                    :disabled="procesando || !docenteElegido[mc.id]"
                    class="shrink-0 rounded-xl bg-blue-50 px-3 text-sm font-bold text-brand hover:bg-blue-100 disabled:opacity-50"
                  >
                    Asignar
                  </button>
                </div>
              </li>
            </ul>
          </section>

          <!-- Alumnos (solo lectura) -->
          <section class="rounded-2xl border border-blue-100 bg-white p-4 shadow-sm">
            <h2 class="font-bold text-slate-900">Alumnos ({{ curso.alumnos.length }})</h2>

            <p v-if="!curso.alumnos.length" class="mt-3 text-sm text-slate-500">Este curso todavía no tiene alumnos.</p>
            <ol v-else class="mt-3 divide-y divide-slate-100 rounded-xl border border-slate-100">
              <li v-for="(a, i) in curso.alumnos" :key="a.id" class="flex items-center gap-3 px-3 py-2">
                <span class="w-6 shrink-0 text-center text-sm font-semibold text-slate-400">{{ i + 1 }}</span>
                <span class="min-w-0 flex-1 truncate text-sm font-semibold text-slate-900">{{ a.alumno_nombre }}</span>
              </li>
            </ol>
          </section>
        </div>
      </template>
    </template>
  </div>
</template>