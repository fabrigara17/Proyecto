<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  agregarMateriasAlCurso, asignarDocente, asignarPreceptor, editarCurso, eliminarCurso,
  getDetalleCurso, getMaterias, quitarDocente, quitarMateriaDelCurso, quitarPreceptor,
} from '@/services/academico'
import { getUsuarios } from '@/services/usuarios'
import { mensajeError } from '@/utils/errores'
import { nombreCompleto } from '@/utils/formato'
import { anioCursada } from '@/utils/texto'
import AppIcon from '@/components/AppIcon.vue'

const route = useRoute()
const router = useRouter()
const cursoId = computed(() => Number(route.params.id))

const curso = ref(null) // detalle: { materias, preceptores, alumnos, ... }
const materias = ref([])
const docentes = ref([])
const preceptores = ref([])

const cargando = ref(true)
const errorCarga = ref('')
const error = ref('')
const exito = ref('')
const procesando = ref(false)

const editando = ref(false)
const formCurso = ref({ nombre: '', anio_cursada: '', anio_lectivo: '' })
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
})

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
          <h1 class="titulo-pagina truncate">{{ curso.nombre }}</h1>
          <p class="text-sm text-slate-500">
            {{ anioCursada(curso.anio_cursada) }} · Año lectivo {{ curso.anio_lectivo }}
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
        <div class="grid gap-3 sm:grid-cols-2">
          <label class="block">
            <span class="text-sm font-semibold text-slate-600">Año de cursada</span>
            <select v-model="formCurso.anio_cursada" class="campo">
              <option value="">Sin especificar</option>
              <option v-for="n in 7" :key="n" :value="n">{{ n }}º año</option>
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

      <!-- Preceptor -->
      <section class="mt-6 rounded-2xl border border-blue-100 bg-white p-4 shadow-sm">
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
  </div>
</template>