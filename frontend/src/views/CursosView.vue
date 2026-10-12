<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { crearCurso, getCursos, getMaterias } from '@/services/academico'
import { mensajeError } from '@/utils/errores'
import { anioCursada } from '@/utils/texto'
import AppIcon from '@/components/AppIcon.vue'

const router = useRouter()

const cursos = ref([])
const materias = ref([])
const cargando = ref(true)
const errorLista = ref('')
const anioFiltro = ref(null)

const mostrarForm = ref(false)
const form = ref(formVacio())
const elegidas = ref([]) // ids de las materias tildadas
const creando = ref(false)
const errorForm = ref('')

function formVacio() {
  return { nombre: '', anio_cursada: '', anio_lectivo: new Date().getFullYear() }
}

const anios = computed(() => [...new Set(cursos.value.map((c) => c.anio_lectivo))].sort((a, b) => b - a))
const filtrados = computed(() =>
  anioFiltro.value === null ? cursos.value : cursos.value.filter((c) => c.anio_lectivo === anioFiltro.value),
)
const todasTildadas = computed(
  () => materias.value.length > 0 && elegidas.value.length === materias.value.length,
)

onMounted(async () => {
  try {
    const [lista, mats] = await Promise.all([getCursos(), getMaterias()])
    cursos.value = lista
    materias.value = mats
  } catch (e) {
    errorLista.value = mensajeError(e, 'No pudimos cargar los cursos. Probá de nuevo.')
  } finally {
    cargando.value = false
  }
})

function alternarTodas() {
  elegidas.value = todasTildadas.value ? [] : materias.value.map((m) => m.id)
}

function cancelar() {
  mostrarForm.value = false
  form.value = formVacio()
  elegidas.value = []
  errorForm.value = ''
}

async function crear() {
  creando.value = true
  errorForm.value = ''
  try {
    const nuevo = await crearCurso({
      nombre: form.value.nombre.trim(),
      anio_cursada: form.value.anio_cursada ? Number(form.value.anio_cursada) : null,
      anio_lectivo: Number(form.value.anio_lectivo),
      materias: elegidas.value,
    })
    // Al crearlo se pasa directo al detalle, para asignar preceptor y profesores
    router.push({ name: 'curso-detalle', params: { id: nuevo.id } })
  } catch (e) {
    errorForm.value = mensajeError(e, 'No se pudo crear el curso.')
  } finally {
    creando.value = false
  }
}
</script>

<template>
  <div class="pagina">
    <div class="flex items-start justify-between gap-3">
      <div>
        <h1 class="titulo-pagina">Cursos</h1>
        <p v-if="!cargando && !errorLista" class="mt-1 text-sm font-semibold text-slate-500">
          {{ filtrados.length }} {{ filtrados.length === 1 ? 'curso' : 'cursos' }}
        </p>
      </div>
      <button v-if="!mostrarForm" type="button" @click="mostrarForm = true" class="boton-principal !w-auto shrink-0 px-4">
        Nuevo curso
      </button>
    </div>

    <!-- Alta de curso -->
    <form
      v-if="mostrarForm"
      @submit.prevent="crear"
      class="mt-4 grid gap-3 rounded-2xl border border-blue-100 bg-white p-4 shadow-sm md:max-w-2xl"
    >
      <h2 class="font-bold text-slate-900">Nuevo curso</h2>

      <label class="block">
        <span class="text-sm font-semibold text-slate-600">Nombre *</span>
        <input v-model="form.nombre" required maxlength="50" placeholder="Ej: 6°M" class="campo" />
      </label>

      <div class="grid gap-3 sm:grid-cols-2">
        <label class="block">
          <span class="text-sm font-semibold text-slate-600">Año de cursada</span>
          <select v-model="form.anio_cursada" class="campo">
            <option value="">Sin especificar</option>
            <option v-for="n in 7" :key="n" :value="n">{{ n }}º año</option>
          </select>
        </label>
        <label class="block">
          <span class="text-sm font-semibold text-slate-600">Año lectivo *</span>
          <input v-model="form.anio_lectivo" required type="number" min="2000" max="2100" class="campo" />
        </label>
      </div>

      <fieldset class="grid gap-2">
        <legend class="text-sm font-semibold text-slate-600">Materias del curso</legend>
        <p v-if="!materias.length" class="text-sm text-slate-500">
          Todavía no hay materias creadas. Podés crearlas en la pestaña Materias y agregarlas después.
        </p>
        <template v-else>
          <label class="flex items-center gap-2 text-sm font-bold text-brand">
            <input type="checkbox" :checked="todasTildadas" @change="alternarTodas" class="size-4" />
            Seleccionar todas ({{ materias.length }})
          </label>
          <div class="grid max-h-56 gap-1 overflow-y-auto rounded-xl border border-slate-200 p-2 sm:grid-cols-2">
            <label v-for="m in materias" :key="m.id" class="flex items-center gap-2 text-sm text-slate-800">
              <input type="checkbox" :value="m.id" v-model="elegidas" class="size-4" />
              {{ m.nombre }}
            </label>
          </div>
          <p class="text-xs text-slate-400">{{ elegidas.length }} elegidas</p>
        </template>
      </fieldset>

      <p v-if="errorForm" role="alert" class="rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-600">
        {{ errorForm }}
      </p>

      <div class="flex gap-3">
        <button type="submit" :disabled="creando" class="boton-principal">
          {{ creando ? 'Creando...' : 'Crear curso' }}
        </button>
        <button type="button" @click="cancelar" class="rounded-xl px-4 font-bold text-slate-500 hover:bg-slate-100">
          Cancelar
        </button>
      </div>
    </form>

    <!-- Filtro por año lectivo -->
    <div v-if="anios.length > 1" class="mt-6 flex flex-wrap items-center gap-2">
      <button
        type="button"
        @click="anioFiltro = null"
        class="rounded-full px-3 py-1 text-sm font-bold transition"
        :class="anioFiltro === null ? 'bg-brand text-white' : 'bg-slate-200/70 text-slate-600'"
      >
        Todos
      </button>
      <button
        v-for="a in anios"
        :key="a"
        type="button"
        @click="anioFiltro = a"
        class="rounded-full px-3 py-1 text-sm font-bold transition"
        :class="anioFiltro === a ? 'bg-brand text-white' : 'bg-slate-200/70 text-slate-600'"
      >
        {{ a }}
      </button>
    </div>

    <p v-if="cargando" class="mt-6 text-slate-500">Cargando...</p>
    <p v-else-if="errorLista" role="alert" class="mt-6 rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-600">
      {{ errorLista }}
    </p>
    <p v-else-if="!filtrados.length" class="mt-6 text-slate-500">Todavía no hay cursos.</p>

    <ul v-else class="mt-5 grid gap-3 md:grid-cols-2 lg:grid-cols-3">
      <li v-for="c in filtrados" :key="c.id">
        <router-link
          :to="{ name: 'curso-detalle', params: { id: c.id } }"
          class="flex items-center gap-4 rounded-2xl border border-blue-100 bg-white p-4 shadow-sm transition hover:border-brand"
        >
          <span class="min-w-0 flex-1">
            <span class="block truncate font-bold text-slate-900">{{ c.nombre }}</span>
            <span class="block text-xs text-slate-500">
              {{ anioCursada(c.anio_cursada) }} · Año lectivo {{ c.anio_lectivo }}
            </span>
            <span class="mt-1 block text-xs font-semibold text-slate-600">
              {{ c.cant_alumnos }} {{ c.cant_alumnos === 1 ? 'alumno' : 'alumnos' }}
              · {{ c.cant_materias }} {{ c.cant_materias === 1 ? 'materia' : 'materias' }}
            </span>
          </span>
          <AppIcon name="arrow-right" class="size-5 shrink-0 text-slate-400" />
        </router-link>
      </li>
    </ul>
  </div>
</template>