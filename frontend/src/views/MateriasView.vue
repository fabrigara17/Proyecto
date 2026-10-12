<script setup>
import { computed, onMounted, ref } from 'vue'
import { crearMateria, getMaterias, getResumenMaterias } from '@/services/academico'
import { mensajeError } from '@/utils/errores'
import { anioCursada, normalizar } from '@/utils/texto'

const resumen = ref([])
const todas = ref([])
const cargando = ref(true)
const errorLista = ref('')

const busqueda = ref('')
const anioFiltro = ref(null)

const mostrarForm = ref(false)
const nueva = ref('')
const creando = ref(false)
const errorForm = ref('')
const exito = ref('')

async function cargar() {
  errorLista.value = ''
  try {
    const [res, mats] = await Promise.all([getResumenMaterias(), getMaterias()])
    resumen.value = res
    todas.value = mats
  } catch (e) {
    errorLista.value = mensajeError(e, 'No pudimos cargar las materias. Probá de nuevo.')
  } finally {
    cargando.value = false
  }
}

onMounted(cargar)

// Una fila por cada materia en cada curso, más las materias que todavía no están en ningún curso
const filas = computed(() => {
  const conCurso = resumen.value.map((r) => ({ ...r, clave: `mc-${r.id}` }))
  const usadas = new Set(resumen.value.map((r) => r.materia))
  const sinCurso = todas.value
    .filter((m) => !usadas.has(m.id))
    .map((m) => ({
      clave: `m-${m.id}`, materia: m.id, materia_nombre: m.nombre,
      curso: null, curso_nombre: null, anio_cursada: null, anio_lectivo: null, docentes: [],
    }))
  return [...conCurso, ...sinCurso].sort((a, b) => a.materia_nombre.localeCompare(b.materia_nombre, 'es'))
})

const aniosPresentes = computed(() =>
  [...new Set(resumen.value.map((r) => r.anio_cursada).filter(Boolean))].sort((a, b) => a - b),
)

const filtradas = computed(() => {
  const q = normalizar(busqueda.value.trim())
  return filas.value.filter((f) => {
    if (anioFiltro.value !== null && f.anio_cursada !== anioFiltro.value) return false
    if (!q) return true
    const texto = normalizar([f.materia_nombre, f.curso_nombre, ...f.docentes.map((d) => d.nombre)].join(' '))
    return texto.includes(q)
  })
})

async function crear() {
  const nombre = nueva.value.trim()
  if (!nombre) return
  creando.value = true
  errorForm.value = ''
  exito.value = ''
  try {
    await crearMateria(nombre)
    exito.value = `Materia "${nombre}" creada. Para que figure en un curso, agregala desde la pestaña Cursos.`
    nueva.value = ''
    mostrarForm.value = false
    await cargar()
  } catch (e) {
    errorForm.value = mensajeError(e, 'No se pudo crear la materia.')
  } finally {
    creando.value = false
  }
}
</script>

<template>
  <div class="pagina">
    <div class="flex items-start justify-between gap-3">
      <div>
        <h1 class="titulo-pagina">Materias</h1>
        <p class="mt-1 text-sm text-slate-500">Cada materia en cada curso, con sus profesores.</p>
      </div>
      <button v-if="!mostrarForm" type="button" @click="mostrarForm = true" class="boton-principal !w-auto shrink-0 px-4">
        Nueva materia
      </button>
    </div>

    <form v-if="mostrarForm" @submit.prevent="crear" class="mt-4 flex gap-2 md:max-w-xl">
      <input v-model="nueva" required maxlength="100" placeholder="Nombre de la materia" class="campo" />
      <button type="submit" :disabled="creando" class="boton-principal !w-auto shrink-0 px-4">
        {{ creando ? 'Creando...' : 'Crear' }}
      </button>
      <button
        type="button"
        @click="mostrarForm = false; nueva = ''; errorForm = ''"
        class="shrink-0 rounded-xl px-3 font-bold text-slate-500 hover:bg-slate-100"
      >
        Cancelar
      </button>
    </form>
    <p v-if="errorForm" role="alert" class="mt-3 rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-600 md:max-w-xl">
      {{ errorForm }}
    </p>
    <p v-if="exito" role="status" class="mt-3 rounded-xl bg-green-50 p-3 text-sm font-semibold text-green-700">
      {{ exito }}
    </p>

    <!-- Filtros -->
    <input
      v-model="busqueda"
      type="search"
      placeholder="Buscar por profesor, materia o curso"
      class="campo mt-5 md:max-w-md"
    />
    <div v-if="aniosPresentes.length" class="mt-3 flex flex-wrap items-center gap-2">
      <button
        type="button"
        @click="anioFiltro = null"
        class="rounded-full px-3 py-1 text-sm font-bold transition"
        :class="anioFiltro === null ? 'bg-brand text-white' : 'bg-slate-200/70 text-slate-600'"
      >
        Todos los años
      </button>
      <button
        v-for="a in aniosPresentes"
        :key="a"
        type="button"
        @click="anioFiltro = a"
        class="rounded-full px-3 py-1 text-sm font-bold transition"
        :class="anioFiltro === a ? 'bg-brand text-white' : 'bg-slate-200/70 text-slate-600'"
      >
        {{ anioCursada(a) }}
      </button>
    </div>

    <p v-if="cargando" class="mt-6 text-slate-500">Cargando...</p>
    <p v-else-if="errorLista" role="alert" class="mt-6 rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-600">
      {{ errorLista }}
    </p>
    <p v-else-if="!filtradas.length" class="mt-6 text-slate-500">No hay materias para mostrar.</p>

    <template v-else>
      <p class="mt-4 text-sm font-semibold text-slate-500">
        {{ filtradas.length }} {{ filtradas.length === 1 ? 'resultado' : 'resultados' }}
      </p>
      <ul class="mt-2 grid gap-2 md:grid-cols-2">
        <li
          v-for="f in filtradas"
          :key="f.clave"
          class="rounded-2xl border border-blue-100 bg-white p-3 shadow-sm"
        >
          <p class="font-bold text-slate-900">{{ f.materia_nombre }}</p>
          <p v-if="f.curso" class="text-xs font-semibold text-slate-500">
            {{ f.curso_nombre }} · {{ anioCursada(f.anio_cursada) }} · {{ f.anio_lectivo }}
          </p>
          <p v-else class="text-xs font-semibold text-amber-600">Sin curso asignado</p>

          <p v-if="f.curso" class="mt-2 text-sm text-slate-700">
            <template v-if="f.docentes.length">{{ f.docentes.map((d) => d.nombre).join(', ') }}</template>
            <span v-else class="font-semibold text-amber-600">Sin profesor asignado</span>
          </p>

          <router-link
            v-if="f.curso"
            :to="{ name: 'curso-detalle', params: { id: f.curso } }"
            class="mt-2 inline-block text-xs font-bold text-brand"
          >
            Ver curso
          </router-link>
        </li>
      </ul>
    </template>
  </div>
</template>