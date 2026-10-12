<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRoute } from 'vue-router'
import {
  getAlumnosDeCurso, getAsistenciasDelDia, getCursosAsignados, getDiasSinClases,
  marcarSinClases, quitarSinClases, tomarAsistencia,
} from '@/services/asistencias'
import { mensajeError } from '@/utils/errores'
import { fechaLarga, nombreCompleto } from '@/utils/formato'
import AppIcon from '@/components/AppIcon.vue'

// Las fechas se manejan como texto YYYY-MM-DD, siempre en hora local
// (toISOString daría la fecha UTC y en Argentina, después de las 21 hs, el día siguiente)
function aISO(d) {
  const mes = String(d.getMonth() + 1).padStart(2, '0')
  const dia = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${mes}-${dia}`
}

function sumarDias(iso, n) {
  const [anio, mes, dia] = iso.split('-').map(Number)
  return aISO(new Date(anio, mes - 1, dia + n))
}

function esFinDeSemana(iso) {
  const [anio, mes, dia] = iso.split('-').map(Number)
  const diaSemana = new Date(anio, mes - 1, dia).getDay()
  return diaSemana === 0 || diaSemana === 6
}

// Mueve la fecha de a un día hábil: salta sábados y domingos
function moverHabil(iso, paso) {
  let f = sumarDias(iso, paso)
  while (esFinDeSemana(f)) f = sumarDias(f, paso)
  return f
}

const route = useRoute()
const hoy = aISO(new Date())
const hoyEsHabil = !esFinDeSemana(hoy)
// Si hoy es sábado o domingo, se arranca en el último día hábil (el viernes)
const diaInicial = hoyEsHabil ? hoy : moverHabil(hoy, -1)

const cursoId = computed(() => Number(route.params.cursoId))
const cursos = ref([])
const fecha = ref(diaInicial)
const alumnos = ref([])
const presentes = ref({}) // { [alumnoId]: true | false }
const yaRegistrada = ref(false)
const modificado = ref(false)
const sinClases = ref(null) // día sin clases que afecta a este curso en esta fecha
const mostrandoSinClases = ref(false)
const motivo = ref('')

const cargandoCurso = ref(true)
const cargandoDia = ref(false)
const guardando = ref(false)
const procesando = ref(false)
const error = ref('')
const exito = ref('')

// Solo existe si el curso es uno de los asignados al preceptor
const cursoActual = computed(() => cursos.value.find((c) => c.id === cursoId.value) ?? null)
const esHoy = computed(() => fecha.value === hoy)
const puedeAvanzar = computed(() => moverHabil(fecha.value, 1) <= hoy)
const cantPresentes = computed(() => alumnos.value.filter((a) => presentes.value[a.id]).length)
const cantAusentes = computed(() => alumnos.value.length - cantPresentes.value)

// Si cambia de día rápido, descartamos las respuestas viejas
let cargaActual = 0

async function cargarDia() {
  if (!cursoActual.value || !fecha.value) return
  const mia = ++cargaActual
  cargandoDia.value = true
  error.value = ''
  exito.value = ''
  try {
    const [lista, registros, dias] = await Promise.all([
      getAlumnosDeCurso(cursoId.value),
      getAsistenciasDelDia(cursoId.value, fecha.value),
      getDiasSinClases(cursoId.value, fecha.value),
    ])
    if (mia !== cargaActual) return
    const previos = new Map(registros.map((r) => [r.alumno, r.presente]))
    alumnos.value = lista
    // Lo ya registrado se respeta; los alumnos sin registro arrancan como presentes
    presentes.value = Object.fromEntries(lista.map((a) => [a.id, previos.get(a.id) ?? true]))
    yaRegistrada.value = registros.length > 0
    sinClases.value = dias[0] ?? null
    mostrandoSinClases.value = false
    motivo.value = ''
    modificado.value = false
  } catch (e) {
    if (mia !== cargaActual) return
    alumnos.value = []
    sinClases.value = null
    error.value = mensajeError(e, 'No pudimos cargar el curso. Probá de nuevo.')
  } finally {
    if (mia === cargaActual) cargandoDia.value = false
  }
}

watch([cursoId, fecha], cargarDia)

onMounted(async () => {
  try {
    cursos.value = await getCursosAsignados()
  } catch (e) {
    error.value = mensajeError(e, 'No pudimos cargar el curso. Probá de nuevo.')
  } finally {
    cargandoCurso.value = false
  }
  await cargarDia()
})

function irADia(nueva) {
  if (nueva === fecha.value || nueva > hoy) return // el backend no acepta fechas futuras
  if (modificado.value && !window.confirm('Tenés cambios sin guardar. ¿Cambiar de día igual?')) return
  fecha.value = nueva
}

function alternar(alumno) {
  presentes.value[alumno.id] = !presentes.value[alumno.id]
  modificado.value = true
  exito.value = ''
}

function marcarTodos(valor) {
  for (const a of alumnos.value) presentes.value[a.id] = valor
  modificado.value = true
  exito.value = ''
}

async function guardar() {
  guardando.value = true
  error.value = ''
  exito.value = ''
  try {
    await tomarAsistencia({
      curso: cursoId.value,
      fecha: fecha.value,
      registros: alumnos.value.map((a) => ({ alumno: a.id, presente: !!presentes.value[a.id] })),
    })
    yaRegistrada.value = true
    modificado.value = false
    exito.value = 'Asistencia guardada.'
  } catch (e) {
    error.value = mensajeError(e, 'No se pudo guardar la asistencia. Probá de nuevo.')
  } finally {
    guardando.value = false
  }
}

async function confirmarSinClases() {
  const hayAsistencia = yaRegistrada.value
  if (
    hayAsistencia &&
    !window.confirm('Ya hay asistencia cargada este día. Si lo marcás sin clases, se borra. ¿Continuar?')
  ) {
    return
  }
  procesando.value = true
  error.value = ''
  exito.value = ''
  try {
    await marcarSinClases({
      curso: cursoId.value,
      fecha: fecha.value,
      motivo: motivo.value.trim(),
      reemplazar: hayAsistencia,
    })
    await cargarDia()
    exito.value = 'Día marcado sin clases.'
  } catch (e) {
    error.value = mensajeError(e, 'No se pudo marcar el día sin clases.')
  } finally {
    procesando.value = false
  }
}

async function habilitarDia() {
  if (!sinClases.value || sinClases.value.curso === null) return
  if (!window.confirm('¿Volver a habilitar este día para tomar asistencia?')) return
  procesando.value = true
  error.value = ''
  exito.value = ''
  try {
    await quitarSinClases(sinClases.value.id)
    await cargarDia()
    exito.value = 'Día habilitado de nuevo.'
  } catch (e) {
    error.value = mensajeError(e, 'No se pudo habilitar el día.')
  } finally {
    procesando.value = false
  }
}

// Evita perder el trabajo si toca "Mis cursos" o cambia de sección sin guardar
onBeforeRouteLeave(() => {
  if (!modificado.value) return true
  return window.confirm('Tenés cambios sin guardar. ¿Salir igual?')
})
</script>

<template>
  <div class="pagina">
    <router-link
      :to="{ name: 'asistencias' }"
      class="inline-flex items-center gap-1 text-sm font-bold text-brand"
    >
      <AppIcon name="arrow-right" class="size-4 rotate-180" />
      Mis cursos
    </router-link>

    <p v-if="cargandoCurso" class="mt-6 text-slate-500">Cargando...</p>

    <p
      v-else-if="!cursoActual"
      role="alert"
      class="mt-6 rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-600"
    >
      {{ error || 'No tenés asignado este curso.' }}
    </p>

    <template v-else>
      <h1 class="titulo-pagina mt-2">{{ cursoActual.nombre }}</h1>
      <p class="text-sm text-slate-500">Año lectivo {{ cursoActual.anio_lectivo }}</p>

      <!-- Selector de día con flechas (salta sábados y domingos) -->
      <div class="mt-4 flex items-center gap-2 md:max-w-2xl">
        <button
          type="button"
          @click="irADia(moverHabil(fecha, -1))"
          aria-label="Día anterior"
          class="grid size-11 shrink-0 place-items-center rounded-xl bg-white text-brand shadow-sm ring-1 ring-slate-100 hover:bg-blue-50"
        >
          <AppIcon name="arrow-right" class="size-5 rotate-180" />
        </button>

        <div class="min-w-0 flex-1 text-center">
          <p class="truncate text-lg font-extrabold text-slate-900 first-letter:uppercase">
            {{ fechaLarga(fecha) }}
          </p>
          <p class="text-xs font-semibold text-slate-500">
            <template v-if="esHoy">Hoy</template>
            <button v-else-if="fecha !== diaInicial" type="button" @click="irADia(diaInicial)" class="font-bold text-brand">
              {{ hoyEsHabil ? 'Ir a hoy' : 'Ir al último día hábil' }}
            </button>
            <template v-else>Último día hábil</template>
          </p>
        </div>

        <button
          type="button"
          @click="irADia(moverHabil(fecha, 1))"
          :disabled="!puedeAvanzar"
          aria-label="Día siguiente"
          class="grid size-11 shrink-0 place-items-center rounded-xl bg-white text-brand shadow-sm ring-1 ring-slate-100 hover:bg-blue-50 disabled:opacity-40 disabled:hover:bg-white"
        >
          <AppIcon name="arrow-right" class="size-5" />
        </button>
      </div>

      <p v-if="cargandoDia" class="mt-6 text-slate-500">Cargando alumnos...</p>

      <!-- Día sin clases -->
      <div
        v-else-if="sinClases"
        class="mt-5 rounded-2xl border border-amber-200 bg-amber-50 p-4 md:max-w-2xl"
      >
        <p class="font-bold text-amber-800">Sin clases</p>
        <p class="mt-0.5 text-sm text-amber-800">
          {{ sinClases.motivo || 'Sin motivo indicado' }}
          · {{ sinClases.curso === null ? 'Todo el colegio' : 'Solo este curso' }}
        </p>
        <button
          v-if="sinClases.curso !== null"
          type="button"
          @click="habilitarDia"
          :disabled="procesando"
          class="mt-2 text-sm font-bold text-brand"
        >
          {{ procesando ? 'Habilitando...' : 'Habilitar el día' }}
        </button>
        <p v-else class="mt-2 text-xs text-amber-700">Lo cargó el administrador.</p>
      </div>

      <p v-else-if="!alumnos.length && !error" class="mt-6 text-slate-500">
        Este curso no tiene alumnos inscriptos.
      </p>

      <template v-else-if="alumnos.length">
        <!-- Resumen -->
        <div class="mt-5 flex flex-wrap items-center gap-x-3 gap-y-1">
          <p class="text-sm font-semibold text-slate-600">
            <span class="text-green-600">{{ cantPresentes }} presentes</span>
            ·
            <span class="text-red-500">{{ cantAusentes }} ausentes</span>
            · {{ alumnos.length }} en total
          </p>
          <span
            class="rounded-full px-2.5 py-0.5 text-xs font-bold"
            :class="yaRegistrada ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'"
          >
            {{ yaRegistrada ? 'Ya registrada' : 'Sin registrar' }}
          </span>
        </div>

        <div class="mt-2 flex flex-wrap gap-4 text-sm font-bold text-brand">
          <button type="button" @click="marcarTodos(true)">Todos presentes</button>
          <button type="button" @click="marcarTodos(false)">Todos ausentes</button>
          <button type="button" @click="mostrandoSinClases = !mostrandoSinClases" class="text-amber-700">
            Marcar sin clases
          </button>
        </div>

        <!-- Formulario de día sin clases -->
        <form
          v-if="mostrandoSinClases"
          @submit.prevent="confirmarSinClases"
          class="mt-3 grid gap-2 rounded-2xl border border-amber-200 bg-amber-50 p-3 md:max-w-2xl"
        >
          <label class="block">
            <span class="text-sm font-semibold text-amber-800">Motivo (opcional)</span>
            <input
              v-model="motivo"
              list="motivos-sin-clases"
              maxlength="100"
              placeholder="Feriado, ausencia docente..."
              class="campo"
            />
            <datalist id="motivos-sin-clases">
              <option value="Feriado" />
              <option value="Ausencia docente" />
              <option value="Jornada institucional" />
              <option value="Paro" />
              <option value="Suspensión por clima" />
            </datalist>
          </label>
          <div class="flex gap-3">
            <button type="submit" :disabled="procesando" class="boton-principal">
              {{ procesando ? 'Guardando...' : 'Marcar sin clases' }}
            </button>
            <button
              type="button"
              @click="mostrandoSinClases = false"
              class="rounded-xl px-4 font-bold text-slate-500 hover:bg-slate-100"
            >
              Cancelar
            </button>
          </div>
        </form>

        <!-- Planilla -->
        <div class="mt-3 overflow-hidden rounded-2xl border border-blue-100 bg-white shadow-sm md:max-w-2xl">
          <table class="w-full table-fixed text-left text-sm">
            <thead class="bg-blue-50 text-xs font-bold uppercase tracking-wide text-slate-500">
              <tr>
                <th scope="col" class="w-12 px-3 py-2.5 text-center">N°</th>
                <th scope="col" class="px-3 py-2.5">Alumno</th>
                <th scope="col" class="w-32 px-3 py-2.5 text-center">Asistencia</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="(a, i) in alumnos" :key="a.id" :class="presentes[a.id] ? '' : 'bg-red-50/60'">
                <td class="px-3 py-2 text-center font-semibold text-slate-400">{{ i + 1 }}</td>
                <td class="truncate px-3 py-2 font-semibold text-slate-900">{{ nombreCompleto(a) }}</td>
                <td class="px-3 py-2 text-center">
                  <button
                    type="button"
                    :aria-pressed="presentes[a.id]"
                    @click="alternar(a)"
                    class="w-24 rounded-full px-3 py-1.5 text-xs font-bold transition"
                    :class="presentes[a.id] ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'"
                  >
                    {{ presentes[a.id] ? 'Presente' : 'Ausente' }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <button
          type="button"
          @click="guardar"
          :disabled="guardando || !alumnos.length"
          class="boton-principal mt-5 md:max-w-sm"
        >
          {{ guardando ? 'Guardando...' : 'Guardar asistencia' }}
        </button>
      </template>

      <p v-if="error" role="alert" class="mt-4 rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-600">
        {{ error }}
      </p>
      <p v-if="exito" role="status" class="mt-4 rounded-xl bg-green-50 p-3 text-sm font-semibold text-green-700">
        {{ exito }}
      </p>
    </template>
  </div>
</template>