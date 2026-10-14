<script setup>
import { onMounted, reactive, ref, watch } from 'vue'
import { crearEtapa, editarEtapa, eliminarEtapa, getEtapas } from '@/services/calificaciones'
import { mensajeError } from '@/utils/errores'

// Las fechas se manejan como texto YYYY-MM-DD, siempre en hora local
function aISO(d) {
  const mes = String(d.getMonth() + 1).padStart(2, '0')
  const dia = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${mes}-${dia}`
}

const fechaAR = (iso) => iso.split('-').reverse().join('/')

const hoy = aISO(new Date())
const anioActual = new Date().getFullYear()
const anios = [anioActual - 1, anioActual, anioActual + 1]
const anio = ref(anioActual)

const etapas = ref([])
const cargando = ref(true)
const guardando = ref(false)
const error = ref('')
const exito = ref('')

const form = reactive({ nombre: '', fecha_inicio: '', fecha_fin: '' })
const editandoId = ref(null)

// Estado de una etapa: lo que ven los docentes
function estadoDe(e) {
  if (!e.habilitada) return { texto: 'Cerrada', clase: 'bg-red-100 text-red-600' }
  if (hoy < e.fecha_inicio) return { texto: 'Aún no comienza', clase: 'bg-slate-100 text-slate-600' }
  if (hoy > e.fecha_fin) return { texto: 'Fuera de fecha', clase: 'bg-amber-100 text-amber-700' }
  return { texto: 'Abierta para cargar notas', clase: 'bg-green-100 text-green-700' }
}

let carga = 0

async function cargar() {
  const mia = ++carga
  cargando.value = true
  try {
    const lista = await getEtapas(anio.value)
    if (mia === carga) etapas.value = lista
  } catch (e) {
    if (mia === carga) error.value = mensajeError(e, 'No pudimos cargar las etapas. Probá de nuevo.')
  } finally {
    if (mia === carga) cargando.value = false
  }
}

function limpiarFormulario() {
  editandoId.value = null
  form.nombre = ''
  form.fecha_inicio = ''
  form.fecha_fin = ''
}

watch(anio, () => {
  limpiarFormulario()
  error.value = ''
  exito.value = ''
  cargar()
})

onMounted(cargar)

function editar(e) {
  editandoId.value = e.id
  form.nombre = e.nombre
  form.fecha_inicio = e.fecha_inicio
  form.fecha_fin = e.fecha_fin
  error.value = ''
  exito.value = ''
}

async function guardar() {
  error.value = ''
  exito.value = ''
  if (!form.nombre.trim() || !form.fecha_inicio || !form.fecha_fin) {
    error.value = 'Completá el nombre y las dos fechas.'
    return
  }
  guardando.value = true
  try {
    const datos = {
      nombre: form.nombre.trim(),
      fecha_inicio: form.fecha_inicio,
      fecha_fin: form.fecha_fin,
    }
    if (editandoId.value) {
      await editarEtapa(editandoId.value, datos)
      exito.value = 'Etapa actualizada.'
    } else {
      await crearEtapa({ ...datos, anio_lectivo: anio.value })
      exito.value = 'Etapa creada.'
    }
    limpiarFormulario()
    await cargar()
  } catch (e) {
    error.value = mensajeError(e, 'No se pudo guardar la etapa.')
  } finally {
    guardando.value = false
  }
}

async function alternar(e) {
  error.value = ''
  exito.value = ''
  try {
    await editarEtapa(e.id, { habilitada: !e.habilitada })
    await cargar()
  } catch (err) {
    error.value = mensajeError(err, 'No se pudo cambiar el estado de la etapa.')
  }
}

async function eliminar(e) {
  if (!window.confirm(`¿Eliminar la etapa "${e.nombre}"?`)) return
  error.value = ''
  exito.value = ''
  try {
    await eliminarEtapa(e.id)
    if (editandoId.value === e.id) limpiarFormulario()
    await cargar()
  } catch (err) {
    error.value = mensajeError(err, 'No se pudo eliminar la etapa.')
  }
}
</script>

<template>
  <div class="pagina">
    <h1 class="titulo-pagina">Etapas de notas</h1>
    <p class="mt-1 text-sm text-slate-500">
      Los docentes solo pueden cargar y modificar notas en las etapas abiertas: las que están habilitadas
      y cuyas fechas incluyen el día de hoy.
    </p>

    <label class="mt-4 block md:max-w-xs">
      <span class="text-sm font-semibold text-slate-600">Año lectivo</span>
      <select v-model.number="anio" class="campo">
        <option v-for="a in anios" :key="a" :value="a">{{ a }}</option>
      </select>
    </label>

    <!-- Alta y edición -->
    <form
      @submit.prevent="guardar"
      class="mt-4 grid gap-3 rounded-2xl border border-blue-100 bg-white p-4 shadow-sm md:grid-cols-4 md:items-end"
    >
      <label class="block">
        <span class="text-sm font-semibold text-slate-600">Nombre</span>
        <input v-model="form.nombre" list="nombres-etapa" maxlength="50" placeholder="1er trimestre" class="campo" />
        <datalist id="nombres-etapa">
          <option value="1er trimestre" />
          <option value="2do trimestre" />
          <option value="3er trimestre" />
          <option value="1er cuatrimestre" />
          <option value="2do cuatrimestre" />
        </datalist>
      </label>
      <label class="block">
        <span class="text-sm font-semibold text-slate-600">Desde</span>
        <input v-model="form.fecha_inicio" type="date" class="campo" />
      </label>
      <label class="block">
        <span class="text-sm font-semibold text-slate-600">Hasta</span>
        <input v-model="form.fecha_fin" type="date" class="campo" />
      </label>
      <div class="flex gap-2">
        <button type="submit" :disabled="guardando" class="boton-principal">
          {{ guardando ? 'Guardando...' : editandoId ? 'Guardar cambios' : 'Crear etapa' }}
        </button>
        <button
          v-if="editandoId"
          type="button"
          @click="limpiarFormulario"
          class="rounded-xl px-4 font-bold text-slate-500 hover:bg-slate-100"
        >
          Cancelar
        </button>
      </div>
    </form>

    <p v-if="error" role="alert" class="mt-3 rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-600">{{ error }}</p>
    <p v-if="exito" role="status" class="mt-3 rounded-xl bg-green-50 p-3 text-sm font-semibold text-green-700">{{ exito }}</p>

    <!-- Listado -->
    <p v-if="cargando" class="mt-6 text-slate-500">Cargando...</p>
    <p v-else-if="!etapas.length" class="mt-6 text-slate-500">
      Todavía no hay etapas en {{ anio }}. Mientras no haya una abierta, los docentes no pueden cargar notas.
    </p>
    <ul v-else class="mt-5 grid gap-3 md:grid-cols-2 lg:grid-cols-3">
      <li v-for="e in etapas" :key="e.id" class="rounded-2xl border border-blue-100 bg-white p-4 shadow-sm">
        <div class="flex items-start justify-between gap-2">
          <p class="font-bold text-slate-900">{{ e.nombre }}</p>
          <span class="shrink-0 rounded-full px-2.5 py-0.5 text-[11px] font-bold" :class="estadoDe(e).clase">
            {{ estadoDe(e).texto }}
          </span>
        </div>
        <p class="mt-1 text-sm text-slate-500">{{ fechaAR(e.fecha_inicio) }} al {{ fechaAR(e.fecha_fin) }}</p>
        <div class="mt-3 flex flex-wrap gap-4 text-sm font-bold">
          <button type="button" @click="alternar(e)" :class="e.habilitada ? 'text-amber-700' : 'text-green-700'">
            {{ e.habilitada ? 'Cerrar' : 'Abrir' }}
          </button>
          <button type="button" @click="editar(e)" class="text-brand">Editar</button>
          <button type="button" @click="eliminar(e)" class="text-red-600">Eliminar</button>
        </div>
      </li>
    </ul>
  </div>
</template>