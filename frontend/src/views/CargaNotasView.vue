<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { getMisMaterias } from '@/services/materiales'
import { getAlumnosDeCurso } from '@/services/asistencias'
import {
  crearCalificacion, editarCalificacion, eliminarCalificacion, getCalificaciones, getEtapas,
} from '@/services/calificaciones'
import { mensajeError } from '@/utils/errores'
import { formatoNota, nombreCompleto } from '@/utils/formato'

const materias = ref([]) // materias que el docente tiene asignadas (cada una en su curso)
const materiaId = ref(null)
const etapas = ref([])
const etapaId = ref(null)
const alumnos = ref([])
const notas = ref([])
const borradores = reactive({}) // { [alumnoId]: { nota, detalle } } para la nota nueva de cada alumno
const editando = ref(null) // { id, alumno, nota, detalle } de la nota que se está corrigiendo

const cargando = ref(true)
const cargandoCurso = ref(false)
const cargandoNotas = ref(false)
const guardando = ref(false)
const error = ref('')
const exito = ref('')

const materiaActual = computed(() => materias.value.find((m) => m.id === materiaId.value) ?? null)
const etapaActual = computed(() => etapas.value.find((e) => e.id === etapaId.value) ?? null)
// Solo se carga y se modifica en etapas abiertas por conducción
const abierta = computed(() => !!etapaActual.value?.esta_abierta)

const notasPorAlumno = computed(() => {
  const mapa = new Map()
  for (const n of notas.value) {
    if (!mapa.has(n.alumno)) mapa.set(n.alumno, [])
    mapa.get(n.alumno).push(n)
  }
  for (const lista of mapa.values()) lista.sort((a, b) => a.fecha.localeCompare(b.fecha) || a.id - b.id)
  return mapa
})

const notasDe = (alumnoId) => notasPorAlumno.value.get(alumnoId) ?? []

function promedioDe(alumnoId) {
  const lista = notasDe(alumnoId)
  if (!lista.length) return '–'
  return formatoNota(lista.reduce((suma, n) => suma + Number(n.nota), 0) / lista.length)
}

function textoEtapa(e) {
  return `${e.nombre}${e.esta_abierta ? ' (abierta)' : ' (cerrada)'}`
}

// Si cambia de materia o de etapa rápido, descartamos las respuestas viejas
let cargaCurso = 0
let cargaNotas = 0

async function cargarMateria() {
  const mc = materiaActual.value
  if (!mc) return
  const mia = ++cargaCurso
  cargandoCurso.value = true
  error.value = ''
  exito.value = ''
  editando.value = null
  try {
    const [lista, listaEtapas] = await Promise.all([
      getAlumnosDeCurso(mc.curso),
      getEtapas(mc.anio_lectivo),
    ])
    if (mia !== cargaCurso) return
    alumnos.value = lista
    etapas.value = listaEtapas
    for (const k of Object.keys(borradores)) delete borradores[k]
    for (const a of lista) borradores[a.id] = { nota: '', detalle: '' }
    // Se arranca por la etapa abierta; si no hay ninguna, por la primera
    etapaId.value = (listaEtapas.find((e) => e.esta_abierta) ?? listaEtapas[0])?.id ?? null
  } catch (e) {
    if (mia !== cargaCurso) return
    alumnos.value = []
    etapas.value = []
    etapaId.value = null
    notas.value = []
    error.value = mensajeError(e, 'No pudimos cargar el curso. Probá de nuevo.')
    return
  } finally {
    if (mia === cargaCurso) cargandoCurso.value = false
  }
  await cargarNotas()
}

async function cargarNotas() {
  const mc = materiaActual.value
  if (!mc || !etapaId.value) {
    notas.value = []
    return
  }
  const mia = ++cargaNotas
  cargandoNotas.value = true
  editando.value = null
  try {
    const lista = await getCalificaciones({ curso: mc.curso, materia: mc.materia, etapa: etapaId.value })
    if (mia === cargaNotas) notas.value = lista
  } catch (e) {
    if (mia === cargaNotas) error.value = mensajeError(e, 'No pudimos cargar las notas. Probá de nuevo.')
  } finally {
    if (mia === cargaNotas) cargandoNotas.value = false
  }
}

async function elegirMateria(valor) {
  materiaId.value = Number(valor)
  await cargarMateria()
}

async function elegirEtapa(valor) {
  etapaId.value = Number(valor)
  error.value = ''
  exito.value = ''
  await cargarNotas()
}

onMounted(async () => {
  try {
    materias.value = await getMisMaterias()
    if (materias.value.length) {
      materiaId.value = materias.value[0].id
      await cargarMateria()
    }
  } catch (e) {
    error.value = mensajeError(e, 'No pudimos cargar tus materias. Probá de nuevo en un momento.')
  } finally {
    cargando.value = false
  }
})

function notaValida(valor) {
  const n = Number(valor)
  return valor !== '' && valor !== null && n >= 1 && n <= 10
}

async function agregar(alumno) {
  const b = borradores[alumno.id]
  error.value = ''
  exito.value = ''
  if (!notaValida(b.nota)) {
    error.value = 'La nota tiene que estar entre 1 y 10.'
    return
  }
  const mc = materiaActual.value
  guardando.value = true
  try {
    const creada = await crearCalificacion({
      alumno: alumno.id,
      materia: mc.materia,
      curso: mc.curso,
      etapa: etapaId.value,
      nota: Number(b.nota),
      detalle: (b.detalle || '').trim(),
    })
    notas.value.push(creada)
    b.nota = ''
    b.detalle = ''
    exito.value = `Nota cargada a ${nombreCompleto(alumno)}.`
  } catch (e) {
    error.value = mensajeError(e, 'No se pudo cargar la nota.')
  } finally {
    guardando.value = false
  }
}

function empezarEdicion(n) {
  if (!abierta.value) return
  editando.value = { id: n.id, alumno: n.alumno, nota: Number(n.nota), detalle: n.detalle }
  error.value = ''
  exito.value = ''
}

async function guardarEdicion() {
  const ed = editando.value
  error.value = ''
  exito.value = ''
  if (!notaValida(ed.nota)) {
    error.value = 'La nota tiene que estar entre 1 y 10.'
    return
  }
  guardando.value = true
  try {
    const actualizada = await editarCalificacion(ed.id, {
      nota: Number(ed.nota),
      detalle: (ed.detalle || '').trim(),
    })
    const i = notas.value.findIndex((n) => n.id === ed.id)
    if (i !== -1) notas.value[i] = actualizada
    editando.value = null
    exito.value = 'Nota actualizada.'
  } catch (e) {
    error.value = mensajeError(e, 'No se pudo modificar la nota.')
  } finally {
    guardando.value = false
  }
}

async function eliminarEdicion() {
  const ed = editando.value
  if (!window.confirm('¿Eliminar esta nota?')) return
  error.value = ''
  exito.value = ''
  guardando.value = true
  try {
    await eliminarCalificacion(ed.id)
    notas.value = notas.value.filter((n) => n.id !== ed.id)
    editando.value = null
    exito.value = 'Nota eliminada.'
  } catch (e) {
    error.value = mensajeError(e, 'No se pudo eliminar la nota.')
  } finally {
    guardando.value = false
  }
}
</script>

<template>
  <div class="pagina">
    <h1 class="titulo-pagina">Cargar notas</h1>
    <p class="mt-1 text-sm text-slate-500">
      Elegí la materia y la etapa. Solo se pueden cargar y modificar notas en etapas abiertas.
    </p>

    <p v-if="cargando" class="mt-6 text-slate-500">Cargando...</p>
    <p v-else-if="error && !materias.length" role="alert" class="mt-6 rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-600">
      {{ error }}
    </p>
    <p v-else-if="!materias.length" class="mt-6 rounded-xl bg-amber-50 p-3 text-sm font-semibold text-amber-700">
      No tenés materias asignadas todavía. Pedile al equipo de conducción que te asigne una.
    </p>

    <template v-else>
      <div class="mt-4 grid gap-3 md:max-w-2xl md:grid-cols-2">
        <label class="block">
          <span class="text-sm font-semibold text-slate-600">Materia</span>
          <select :value="materiaId" @change="elegirMateria($event.target.value)" class="campo">
            <option v-for="m in materias" :key="m.id" :value="m.id">{{ m.materia_nombre }} · {{ m.curso_nombre }}</option>
          </select>
        </label>

        <label class="block">
          <span class="text-sm font-semibold text-slate-600">Etapa</span>
          <select :value="etapaId" @change="elegirEtapa($event.target.value)" :disabled="!etapas.length" class="campo">
            <option v-for="e in etapas" :key="e.id" :value="e.id">{{ textoEtapa(e) }}</option>
          </select>
        </label>
      </div>

      <p v-if="cargandoCurso" class="mt-6 text-slate-500">Cargando alumnos...</p>

      <p v-else-if="!etapas.length" class="mt-4 rounded-xl bg-amber-50 p-3 text-sm font-semibold text-amber-700 md:max-w-2xl">
        El equipo de conducción todavía no cargó etapas para este año lectivo, así que por ahora no se pueden cargar notas.
      </p>

      <template v-else>
        <p
          v-if="!abierta"
          class="mt-4 rounded-xl bg-slate-100 p-3 text-sm font-semibold text-slate-600 md:max-w-2xl"
        >
          Esta etapa no está habilitada para cargar ni modificar notas: solo se pueden consultar.
        </p>

        <p v-if="error" role="alert" class="mt-3 rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-600 md:max-w-2xl">{{ error }}</p>
        <p v-if="exito" role="status" class="mt-3 rounded-xl bg-green-50 p-3 text-sm font-semibold text-green-700 md:max-w-2xl">{{ exito }}</p>

        <p v-if="cargandoNotas" class="mt-6 text-slate-500">Cargando notas...</p>
        <p v-else-if="!alumnos.length" class="mt-6 text-slate-500">Este curso no tiene alumnos inscriptos.</p>

        <ul v-else class="mt-4 grid gap-3 md:max-w-3xl">
          <li v-for="a in alumnos" :key="a.id" class="rounded-2xl border border-blue-100 bg-white p-4 shadow-sm">
            <div class="flex items-start justify-between gap-3">
              <p class="font-bold text-slate-900">{{ nombreCompleto(a) }}</p>
              <p class="shrink-0 text-sm text-slate-500">
                Promedio <span class="font-extrabold text-brand">{{ promedioDe(a.id) }}</span>
              </p>
            </div>

            <!-- Notas ya cargadas -->
            <div class="mt-2 flex flex-wrap items-center gap-2">
              <p v-if="!notasDe(a.id).length" class="text-sm text-slate-400">Sin notas en esta etapa.</p>
              <button
                v-for="n in notasDe(a.id)"
                :key="n.id"
                type="button"
                :disabled="!abierta"
                @click="empezarEdicion(n)"
                class="rounded-xl px-2.5 py-1.5 text-center transition"
                :class="[
                  editando?.id === n.id ? 'bg-brand text-white' : 'bg-blue-50 text-brand',
                  abierta ? 'hover:bg-blue-100' : 'cursor-default',
                ]"
                :title="abierta ? 'Tocá para corregir o eliminar' : ''"
              >
                <span class="block text-base font-extrabold">{{ formatoNota(n.nota) }}</span>
                <span v-if="n.detalle" class="block text-[10px] font-semibold opacity-80">{{ n.detalle }}</span>
              </button>
            </div>

            <!-- Corregir una nota -->
            <form
              v-if="editando && editando.alumno === a.id"
              @submit.prevent="guardarEdicion"
              class="mt-3 flex flex-wrap items-center gap-2 rounded-xl bg-slate-50 p-3"
            >
              <input
                v-model.number="editando.nota"
                type="number" min="1" max="10" step="0.01" aria-label="Nota"
                class="w-24 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-brand focus:ring-2 focus:ring-brand/20"
              />
              <input
                v-model="editando.detalle"
                maxlength="100" placeholder="Detalle (opcional)" aria-label="Detalle"
                class="min-w-0 flex-1 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-brand focus:ring-2 focus:ring-brand/20"
              />
              <button type="submit" :disabled="guardando" class="rounded-xl bg-brand px-4 py-2 text-sm font-bold text-white disabled:opacity-60">
                Guardar
              </button>
              <button type="button" @click="eliminarEdicion" :disabled="guardando" class="px-2 text-sm font-bold text-red-600">
                Eliminar
              </button>
              <button type="button" @click="editando = null" class="px-2 text-sm font-bold text-slate-500">Cancelar</button>
            </form>

            <!-- Nota nueva -->
            <form
              v-if="abierta && borradores[a.id]"
              @submit.prevent="agregar(a)"
              class="mt-3 flex flex-wrap items-center gap-2"
            >
              <input
                v-model.number="borradores[a.id].nota"
                type="number" min="1" max="10" step="0.01" placeholder="Nota" aria-label="Nota nueva"
                class="w-24 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-brand focus:ring-2 focus:ring-brand/20"
              />
              <input
                v-model="borradores[a.id].detalle"
                maxlength="100" placeholder="Detalle (ej. Parcial 1)" aria-label="Detalle"
                class="min-w-0 flex-1 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-brand focus:ring-2 focus:ring-brand/20"
              />
              <button type="submit" :disabled="guardando" class="rounded-xl bg-brand px-4 py-2 text-sm font-bold text-white disabled:opacity-60">
                Agregar
              </button>
            </form>
          </li>
        </ul>
      </template>
    </template>
  </div>
</template>