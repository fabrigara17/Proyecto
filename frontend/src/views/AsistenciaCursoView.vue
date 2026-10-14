<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  getAlumnosDeCurso, getAsistenciasDeClase, getCursosAsignados, getDiasSinClases, getHorarios,
  marcarSinClases, quitarSinClases, tomarAsistencia,
} from '@/services/asistencias'
import { mensajeError } from '@/utils/errores'
import { fechaLarga, nombreCompleto } from '@/utils/formato'
import AppIcon from '@/components/AppIcon.vue'

const ESTADOS = [
  { valor: 'PRESENTE', corto: 'P', texto: 'Presente', activo: 'bg-green-100 text-green-700', fila: '' },
  { valor: 'AUSENTE', corto: 'A', texto: 'Ausente', activo: 'bg-red-100 text-red-600', fila: 'bg-red-50/60' },
  { valor: 'TARDE', corto: 'T', texto: 'Llegada tarde', activo: 'bg-amber-100 text-amber-700', fila: 'bg-amber-50/60' },
  { valor: 'RETIRO', corto: 'R', texto: 'Retiro anticipado', activo: 'bg-blue-100 text-blue-700', fila: 'bg-blue-50/60' },
]
const ESTADO_POR_VALOR = Object.fromEntries(ESTADOS.map((e) => [e.valor, e]))

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

// Día de la semana como lo usa el backend: 0 = lunes ... 4 = viernes
function diaSemanaDe(iso) {
  const [anio, mes, dia] = iso.split('-').map(Number)
  return (new Date(anio, mes - 1, dia).getDay() + 6) % 7
}

// Mueve la fecha de a un día hábil: salta sábados y domingos
function moverHabil(iso, paso) {
  let f = sumarDias(iso, paso)
  while (esFinDeSemana(f)) f = sumarDias(f, paso)
  return f
}

const route = useRoute()
const auth = useAuthStore()
const hoy = aISO(new Date())
const hoyEsHabil = !esFinDeSemana(hoy)
// Si hoy es sábado o domingo, se arranca en el último día hábil (el viernes)
const diaInicial = hoyEsHabil ? hoy : moverHabil(hoy, -1)

const cursoId = computed(() => Number(route.params.cursoId))
const cursos = ref([])
const fecha = ref(diaInicial)
const alumnos = ref([])
const clases = ref([]) // clases del horario que tiene el curso ese día de la semana
const claseId = ref(null)
const estados = ref({}) // { [alumnoId]: 'PRESENTE' | 'AUSENTE' | 'TARDE' | 'RETIRO' }
const yaRegistrada = ref(false)
const modificado = ref(false)
const sinClases = ref(null) // día sin clases que afecta a este curso en esta fecha
const mostrandoSinClases = ref(false)
const motivo = ref('')

const cargandoCurso = ref(true)
const cargandoDia = ref(false)
const cargandoClase = ref(false)
const guardando = ref(false)
const procesando = ref(false)
const error = ref('')
const exito = ref('')

// Solo existe si el curso es uno de los asignados al usuario
const cursoActual = computed(() => cursos.value.find((c) => c.id === cursoId.value) ?? null)
const claseActual = computed(() => clases.value.find((c) => c.id === claseId.value) ?? null)
const esHoy = computed(() => fecha.value === hoy)
// La asistencia solo se modifica el mismo día: al terminar, queda cerrada
const soloLectura = computed(() => fecha.value !== hoy)
const puedeAvanzar = computed(() => moverHabil(fecha.value, 1) <= hoy)
const esPreceptor = computed(() => auth.rol === 'PRECEPTOR')
const resumen = computed(() =>
  ESTADOS.map((e) => ({
    ...e,
    cantidad: alumnos.value.filter((a) => estados.value[a.id] === e.valor).length,
  })),
)

// Si cambia de día o de clase rápido, descartamos las respuestas viejas
let cargaDia = 0
let cargaClase = 0

async function cargarDia() {
  if (!cursoActual.value || !fecha.value) return
  const mia = ++cargaDia
  cargandoDia.value = true
  error.value = ''
  exito.value = ''
  try {
    const [lista, horario, dias] = await Promise.all([
      getAlumnosDeCurso(cursoId.value),
      getHorarios(cursoId.value, diaSemanaDe(fecha.value)),
      getDiasSinClases(cursoId.value, fecha.value),
    ])
    if (mia !== cargaDia) return
    alumnos.value = lista
    clases.value = horario
    sinClases.value = dias[0] ?? null
    mostrandoSinClases.value = false
    motivo.value = ''
    // Se mantiene la clase elegida si sigue en la lista; si no, se arranca por la primera
    if (!horario.some((c) => c.id === claseId.value)) claseId.value = horario[0]?.id ?? null
    modificado.value = false
  } catch (e) {
    if (mia !== cargaDia) return
    alumnos.value = []
    clases.value = []
    claseId.value = null
    sinClases.value = null
    error.value = mensajeError(e, 'No pudimos cargar el curso. Probá de nuevo.')
    return
  } finally {
    if (mia === cargaDia) cargandoDia.value = false
  }
  await cargarClase()
}

async function cargarClase() {
  const mia = ++cargaClase
  if (!claseId.value) {
    estados.value = {}
    yaRegistrada.value = false
    modificado.value = false
    return
  }
  cargandoClase.value = true
  try {
    const registros = await getAsistenciasDeClase(claseId.value, fecha.value)
    if (mia !== cargaClase) return
    const previos = new Map(registros.map((r) => [r.alumno, r.estado]))
    // Lo ya registrado se respeta; los alumnos sin registro arrancan como presentes
    estados.value = Object.fromEntries(alumnos.value.map((a) => [a.id, previos.get(a.id) ?? 'PRESENTE']))
    yaRegistrada.value = registros.length > 0
    modificado.value = false
  } catch (e) {
    if (mia !== cargaClase) return
    error.value = mensajeError(e, 'No pudimos cargar la asistencia de la clase. Probá de nuevo.')
  } finally {
    if (mia === cargaClase) cargandoClase.value = false
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

async function elegirClase(id) {
  if (id === claseId.value) return
  if (modificado.value && !window.confirm('Tenés cambios sin guardar. ¿Cambiar de clase igual?')) return
  claseId.value = id
  exito.value = ''
  error.value = ''
  await cargarClase()
}

function marcar(alumno, estado) {
  if (soloLectura.value) return
  estados.value[alumno.id] = estado
  modificado.value = true
  exito.value = ''
}

function marcarTodos(estado) {
  for (const a of alumnos.value) estados.value[a.id] = estado
  modificado.value = true
  exito.value = ''
}

async function guardar() {
  guardando.value = true
  error.value = ''
  exito.value = ''
  try {
    await tomarAsistencia({
      clase: claseId.value,
      fecha: fecha.value,
      registros: alumnos.value.map((a) => ({ alumno: a.id, estado: estados.value[a.id] })),
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
  if (!window.confirm('Si ya hay asistencia cargada este día en este curso, se borra. ¿Marcar el día sin clases?')) {
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
      reemplazar: true,
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

      <p v-if="soloLectura" class="mt-3 rounded-xl bg-slate-100 p-3 text-sm font-semibold text-slate-600 md:max-w-2xl">
        Este día ya terminó: la asistencia quedó cerrada y solo se puede consultar.
      </p>

      <p v-if="cargandoDia" class="mt-6 text-slate-500">Cargando...</p>

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
          v-if="esPreceptor && sinClases.curso !== null"
          type="button"
          @click="habilitarDia"
          :disabled="procesando"
          class="mt-2 text-sm font-bold text-brand"
        >
          {{ procesando ? 'Habilitando...' : 'Habilitar el día' }}
        </button>
        <p v-else-if="sinClases.curso === null" class="mt-2 text-xs text-amber-700">Lo cargó el administrador.</p>
      </div>

      <!-- Sin horario cargado para ese día -->
      <div
        v-else-if="!clases.length"
        class="mt-5 rounded-2xl border border-slate-200 bg-white p-4 md:max-w-2xl"
      >
        <p class="font-bold text-slate-800">No hay clases cargadas para este día</p>
        <p class="mt-0.5 text-sm text-slate-500">
          El horario del curso todavía no tiene clases ese día de la semana.
        </p>
        <router-link v-if="esPreceptor" :to="{ name: 'horarios' }" class="mt-2 inline-block text-sm font-bold text-brand">
          Armar el horario
        </router-link>
        <div v-if="esPreceptor && !soloLectura" class="mt-3">
          <button type="button" @click="mostrandoSinClases = !mostrandoSinClases" class="text-sm font-bold text-amber-700">
            Marcar sin clases
          </button>
        </div>
      </div>

      <template v-else>
        <!-- Clases del día -->
        <div class="mt-4 flex flex-wrap gap-2 md:max-w-2xl">
          <button
            v-for="c in clases"
            :key="c.id"
            type="button"
            @click="elegirClase(c.id)"
            class="rounded-xl px-3 py-2 text-left text-sm transition"
            :class="c.id === claseId
              ? 'bg-brand text-white shadow-sm'
              : 'bg-white text-slate-700 ring-1 ring-slate-200 hover:bg-blue-50'"
          >
            <span class="block text-[11px] font-bold opacity-80">{{ c.hora_inicio }} a {{ c.hora_fin }} hs</span>
            <span class="block font-bold">{{ c.materia_nombre }}</span>
          </button>
        </div>

        <p v-if="!alumnos.length && !error" class="mt-6 text-slate-500">
          Este curso no tiene alumnos inscriptos.
        </p>

        <p v-else-if="cargandoClase" class="mt-6 text-slate-500">Cargando asistencia...</p>

        <p
          v-else-if="soloLectura && !yaRegistrada"
          class="mt-6 rounded-xl bg-slate-100 p-3 text-sm font-semibold text-slate-600 md:max-w-2xl"
        >
          No se registró asistencia en esta clase.
        </p>

        <template v-else-if="alumnos.length">
          <!-- Resumen -->
          <div class="mt-5 flex flex-wrap items-center gap-x-3 gap-y-1">
            <p class="text-sm font-semibold text-slate-600">
              <template v-for="(r, i) in resumen" :key="r.valor">
                <span v-if="i" class="text-slate-300"> · </span>
                <span :class="r.activo.split(' ')[1]">{{ r.cantidad }} {{ r.texto.toLowerCase() }}</span>
              </template>
              · {{ alumnos.length }} en total
            </p>
            <span
              class="rounded-full px-2.5 py-0.5 text-xs font-bold"
              :class="yaRegistrada ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'"
            >
              {{ yaRegistrada ? 'Ya registrada' : 'Sin registrar' }}
            </span>
          </div>

          <div v-if="!soloLectura" class="mt-2 flex flex-wrap gap-4 text-sm font-bold text-brand">
            <button type="button" @click="marcarTodos('PRESENTE')">Todos presentes</button>
            <button type="button" @click="marcarTodos('AUSENTE')">Todos ausentes</button>
            <button
              v-if="esPreceptor"
              type="button"
              @click="mostrandoSinClases = !mostrandoSinClases"
              class="text-amber-700"
            >
              Marcar sin clases
            </button>
          </div>

          <!-- Planilla -->
          <div class="mt-3 overflow-hidden rounded-2xl border border-blue-100 bg-white shadow-sm md:max-w-2xl">
            <table class="w-full table-fixed text-left text-sm">
              <thead class="bg-blue-50 text-xs font-bold uppercase tracking-wide text-slate-500">
                <tr>
                  <th scope="col" class="w-10 px-2 py-2.5 text-center">N°</th>
                  <th scope="col" class="px-2 py-2.5">Alumno</th>
                  <th scope="col" class="w-44 px-2 py-2.5 text-center">Asistencia</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100">
                <tr v-for="(a, i) in alumnos" :key="a.id" :class="ESTADO_POR_VALOR[estados[a.id]]?.fila">
                  <td class="px-2 py-2 text-center font-semibold text-slate-400">{{ i + 1 }}</td>
                  <td class="truncate px-2 py-2 font-semibold text-slate-900">{{ nombreCompleto(a) }}</td>
                  <td class="px-2 py-2">
                    <!-- Solo lectura: se muestra el estado registrado -->
                    <span
                      v-if="soloLectura"
                      class="mx-auto block w-fit rounded-full px-3 py-1 text-xs font-bold"
                      :class="ESTADO_POR_VALOR[estados[a.id]]?.activo"
                    >
                      {{ ESTADO_POR_VALOR[estados[a.id]]?.texto }}
                    </span>
                    <!-- Hoy: un botón por estado -->
                    <div v-else class="flex justify-center gap-1" role="group" :aria-label="`Asistencia de ${nombreCompleto(a)}`">
                      <button
                        v-for="e in ESTADOS"
                        :key="e.valor"
                        type="button"
                        :title="e.texto"
                        :aria-label="e.texto"
                        :aria-pressed="estados[a.id] === e.valor"
                        @click="marcar(a, e.valor)"
                        class="size-8 rounded-full text-xs font-bold transition"
                        :class="estados[a.id] === e.valor ? e.activo : 'bg-slate-100 text-slate-400 hover:bg-slate-200'"
                      >
                        {{ e.corto }}
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <p v-if="!soloLectura" class="mt-2 text-xs text-slate-500 md:max-w-2xl">
            P: presente · A: ausente · T: llegada tarde · R: retiro anticipado
          </p>

          <button
            v-if="!soloLectura"
            type="button"
            @click="guardar"
            :disabled="guardando || !alumnos.length"
            class="boton-principal mt-5 md:max-w-sm"
          >
            {{ guardando ? 'Guardando...' : 'Guardar asistencia' }}
          </button>
        </template>
      </template>

      <!-- Formulario de día sin clases (solo preceptor) -->
      <form
        v-if="mostrandoSinClases && esPreceptor"
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

      <p v-if="error" role="alert" class="mt-4 rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-600">
        {{ error }}
      </p>
      <p v-if="exito" role="status" class="mt-4 rounded-xl bg-green-50 p-3 text-sm font-semibold text-green-700">
        {{ exito }}
      </p>
    </template>
  </div>
</template>