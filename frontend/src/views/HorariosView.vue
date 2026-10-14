<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import {
  crearClase, eliminarClase, getCursosAsignados, getHorarios, getMateriasDeMisCursos,
} from '@/services/asistencias'
import { mensajeError } from '@/utils/errores'

const DIAS = [
  { valor: 0, texto: 'Lunes' },
  { valor: 1, texto: 'Martes' },
  { valor: 2, texto: 'Miércoles' },
  { valor: 3, texto: 'Jueves' },
  { valor: 4, texto: 'Viernes' },
]

const cursos = ref([])
const materias = ref([])
const cursoId = ref(null)
const clases = ref([])

const cargando = ref(true)
const cargandoClases = ref(false)
const guardando = ref(false)
const error = ref('')
const exito = ref('')

const form = reactive({ dia_semana: 0, materia_curso: '', hora_inicio: '', hora_fin: '' })

// Solo las materias del plan del curso elegido
const materiasDelCurso = computed(() => materias.value.filter((m) => m.curso === cursoId.value))

const clasesPorDia = computed(() =>
  DIAS.map((d) => ({ ...d, clases: clases.value.filter((c) => c.dia_semana === d.valor) })),
)

let carga = 0

async function cargarClases() {
  if (!cursoId.value) return
  const mia = ++carga
  cargandoClases.value = true
  try {
    const lista = await getHorarios(cursoId.value)
    if (mia === carga) clases.value = lista
  } catch (e) {
    if (mia === carga) error.value = mensajeError(e, 'No pudimos cargar el horario. Probá de nuevo.')
  } finally {
    if (mia === carga) cargandoClases.value = false
  }
}

watch(cursoId, () => {
  form.materia_curso = ''
  error.value = ''
  exito.value = ''
  cargarClases()
})

onMounted(async () => {
  try {
    const [c, m] = await Promise.all([getCursosAsignados(), getMateriasDeMisCursos()])
    cursos.value = c
    materias.value = m
    if (c.length) cursoId.value = c[0].id
  } catch (e) {
    error.value = mensajeError(e, 'No pudimos cargar tus cursos. Probá de nuevo en un momento.')
  } finally {
    cargando.value = false
  }
})

async function agregar() {
  error.value = ''
  exito.value = ''
  if (!form.materia_curso || !form.hora_inicio || !form.hora_fin) {
    error.value = 'Elegí la materia y completá la hora de inicio y de fin.'
    return
  }
  guardando.value = true
  try {
    await crearClase({
      curso: cursoId.value,
      materia_curso: form.materia_curso,
      dia_semana: form.dia_semana,
      hora_inicio: form.hora_inicio,
      hora_fin: form.hora_fin,
    })
    await cargarClases()
    // Para cargar clases seguidas: la próxima arranca cuando terminó esta
    form.hora_inicio = form.hora_fin
    form.hora_fin = ''
    exito.value = 'Clase agregada.'
  } catch (e) {
    error.value = mensajeError(e, 'No se pudo agregar la clase.')
  } finally {
    guardando.value = false
  }
}

async function quitar(clase) {
  if (!window.confirm(`¿Quitar ${clase.materia_nombre} (${clase.hora_inicio} a ${clase.hora_fin}) del horario?`)) return
  error.value = ''
  exito.value = ''
  try {
    await eliminarClase(clase.id)
    await cargarClases()
  } catch (e) {
    error.value = mensajeError(e, 'No se pudo quitar la clase.')
  }
}
</script>

<template>
  <div class="pagina">
    <h1 class="titulo-pagina">Horarios</h1>
    <p class="mt-1 text-sm text-slate-500">
      Armá el horario semanal de cada curso. Con él se toma la asistencia por materia.
    </p>

    <p v-if="cargando" class="mt-6 text-slate-500">Cargando...</p>
    <p v-else-if="error && !cursos.length" role="alert" class="mt-6 rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-600">
      {{ error }}
    </p>
    <p v-else-if="!cursos.length" class="mt-6 rounded-xl bg-amber-50 p-3 text-sm font-semibold text-amber-700">
      No tenés cursos asignados todavía.
    </p>

    <template v-else>
      <label class="mt-4 block md:max-w-sm">
        <span class="text-sm font-semibold text-slate-600">Curso</span>
        <select v-model.number="cursoId" class="campo">
          <option v-for="c in cursos" :key="c.id" :value="c.id">{{ c.nombre }} · {{ c.anio_lectivo }}</option>
        </select>
      </label>

      <!-- Agregar una clase -->
      <form
        @submit.prevent="agregar"
        class="mt-4 grid gap-3 rounded-2xl border border-blue-100 bg-white p-4 shadow-sm md:grid-cols-5 md:items-end"
      >
        <label class="block">
          <span class="text-sm font-semibold text-slate-600">Día</span>
          <select v-model.number="form.dia_semana" class="campo">
            <option v-for="d in DIAS" :key="d.valor" :value="d.valor">{{ d.texto }}</option>
          </select>
        </label>

        <label class="block md:col-span-2">
          <span class="text-sm font-semibold text-slate-600">Materia</span>
          <select v-model.number="form.materia_curso" class="campo">
            <option value="" disabled>Elegí una materia</option>
            <option v-for="m in materiasDelCurso" :key="m.id" :value="m.id">{{ m.materia_nombre }}</option>
          </select>
        </label>

        <div class="grid grid-cols-2 gap-3">
          <label class="block">
            <span class="text-sm font-semibold text-slate-600">Desde</span>
            <input v-model="form.hora_inicio" type="time" class="campo" />
          </label>
          <label class="block">
            <span class="text-sm font-semibold text-slate-600">Hasta</span>
            <input v-model="form.hora_fin" type="time" class="campo" />
          </label>
        </div>

        <button type="submit" :disabled="guardando" class="boton-principal">
          {{ guardando ? 'Agregando...' : 'Agregar clase' }}
        </button>
      </form>

      <p v-if="!materiasDelCurso.length" class="mt-3 text-sm font-semibold text-amber-700">
        Este curso todavía no tiene materias cargadas en su plan de estudios.
      </p>

      <p v-if="error" role="alert" class="mt-3 rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-600">{{ error }}</p>
      <p v-if="exito" role="status" class="mt-3 rounded-xl bg-green-50 p-3 text-sm font-semibold text-green-700">{{ exito }}</p>

      <!-- Horario de la semana -->
      <p v-if="cargandoClases" class="mt-6 text-slate-500">Cargando horario...</p>
      <div v-else class="mt-5 grid gap-3 md:grid-cols-5">
        <section
          v-for="d in clasesPorDia"
          :key="d.valor"
          class="rounded-2xl border border-blue-100 bg-white p-3 shadow-sm"
        >
          <h2 class="text-sm font-extrabold uppercase tracking-wide text-brand">{{ d.texto }}</h2>

          <p v-if="!d.clases.length" class="mt-2 text-xs text-slate-400">Sin clases cargadas.</p>
          <ul v-else class="mt-2 grid gap-2">
            <li v-for="c in d.clases" :key="c.id" class="rounded-xl bg-blue-50 p-2.5">
              <p class="text-xs font-bold text-slate-500">{{ c.hora_inicio }} a {{ c.hora_fin }} hs</p>
              <p class="font-bold text-slate-900">{{ c.materia_nombre }}</p>
              <p v-if="c.docentes.length" class="truncate text-xs text-slate-500">{{ c.docentes.join(' · ') }}</p>
              <button type="button" @click="quitar(c)" class="mt-1 text-xs font-bold text-red-600">Quitar</button>
            </li>
          </ul>
        </section>
      </div>
    </template>
  </div>
</template>