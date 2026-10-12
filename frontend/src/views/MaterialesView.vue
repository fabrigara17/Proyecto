<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  eliminarMaterial, getMateriales, getMisMaterias, subirMaterial, descargarMaterial
} from '@/services/materiales'
import { fechaCorta } from '@/utils/formato'
import AppIcon from '@/components/AppIcon.vue'
import ChatConsultas from '@/components/ChatConsultas.vue'

const MAX_MB = 10
const EXTENSIONES = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'jpg', 'jpeg', 'png', 'txt']
const aceptar = EXTENSIONES.map((e) => `.${e}`).join(',')

const auth = useAuthStore()
const route = useRoute()
const puedeSubir = computed(() => ['DOCENTE', 'ADMIN'].includes(auth.rol))

const materiales = ref([])
const misMaterias = ref([])
const cargando = ref(true)
const error = ref('')

// Consultas: qué materiales tienen el chat abierto y cuál viene resaltado desde un aviso
const abiertos = ref({})
const destacado = ref(null)

// Formulario
const titulo = ref('')
const descripcion = ref('')
const materiaCurso = ref('')
const archivo = ref(null)
const inputArchivo = ref(null)
const enviando = ref(false)
const errorForm = ref('')
const exito = ref('')
const errorAccion = ref('')
const descargando = ref(null)

async function descargar(m) {
  errorAccion.value = ''
  descargando.value = m.id
  try {
    await descargarMaterial(m)
  } catch {
    errorAccion.value = 'No se pudo descargar el archivo. Probá de nuevo.'
  } finally {
    descargando.value = null
  }
}

const tamano = computed(() => {
  if (!archivo.value) return ''
  const mb = archivo.value.size / 1024 / 1024
  return mb >= 1 ? `${mb.toFixed(1)} MB` : `${Math.max(1, Math.round(archivo.value.size / 1024))} KB`
})

onMounted(async () => {
  try {
    const [lista, materias] = await Promise.all([
      getMateriales(),
      puedeSubir.value ? getMisMaterias() : Promise.resolve([]),
    ])
    materiales.value = lista
    misMaterias.value = materias
    if (materias.length === 1) materiaCurso.value = materias[0].id
  } catch {
    error.value = 'No pudimos cargar los materiales. Probá de nuevo en un momento.'
  } finally {
    cargando.value = false
  }
  await abrirDesdeAviso()
})

// Si venimos de un aviso (/materiales?material=ID), abrimos ese material y mostramos sus consultas
async function abrirDesdeAviso() {
  const id = Number(route.query.material)
  if (!id || !materiales.value.some((m) => m.id === id)) return
  abiertos.value[id] = true
  destacado.value = id
  await nextTick()
  document.getElementById(`material-${id}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  setTimeout(() => (destacado.value = null), 3000)
}

function alternarConsultas(m) {
  abiertos.value[m.id] = !abiertos.value[m.id]
}

function limpiarArchivo() {
  archivo.value = null
  if (inputArchivo.value) inputArchivo.value.value = ''
}

function elegirArchivo(e) {
  errorForm.value = ''
  exito.value = ''
  const f = e.target.files[0]
  if (!f) {
    archivo.value = null
    return
  }
  const ext = f.name.split('.').pop().toLowerCase()
  if (!EXTENSIONES.includes(ext)) {
    errorForm.value = `Tipo de archivo no permitido. Podés subir: ${EXTENSIONES.join(', ')}.`
    limpiarArchivo()
    return
  }
  if (f.size > MAX_MB * 1024 * 1024) {
    errorForm.value = `El archivo supera los ${MAX_MB} MB.`
    limpiarArchivo()
    return
  }
  archivo.value = f
}

async function enviar() {
  errorForm.value = ''
  exito.value = ''
  if (!archivo.value) {
    errorForm.value = 'Elegí un archivo para subir.'
    return
  }
  enviando.value = true
  try {
    const nuevo = await subirMaterial({
      titulo: titulo.value.trim(),
      descripcion: descripcion.value.trim(),
      materiaCurso: materiaCurso.value,
      archivo: archivo.value,
    })
    materiales.value.unshift(nuevo)
    titulo.value = ''
    descripcion.value = ''
    limpiarArchivo()
    exito.value = 'Material subido correctamente.'
  } catch (e) {
    const data = e.response?.data
    errorForm.value = data && typeof data === 'object'
      ? Object.values(data).flat().join(' ')
      : 'No se pudo subir el archivo. Probá de nuevo.'
  } finally {
    enviando.value = false
  }
}

async function eliminar(m) {
  if (!confirm(`¿Eliminar "${m.titulo}"? Se borran también sus consultas.`)) return
  try {
    await   Material(m.id)
    materiales.value = materiales.value.filter((x) => x.id !== m.id)
  } catch {
    error.value = 'No se pudo eliminar el material. Probá de nuevo.'
  }
}
</script>

<template>
  <div class="pagina">
    <h1 class="titulo-pagina">Materiales</h1>
    <p class="mt-1 text-sm text-slate-500">
      {{ puedeSubir ? 'Subí archivos para tus cursos y respondé las consultas de las familias.' : 'Archivos que subieron los docentes. Podés dejar tus consultas en cada uno.' }}
    </p>

    <!-- Formulario: solo docentes -->
    <form
      v-if="puedeSubir"
      @submit.prevent="enviar"
      class="mt-5 space-y-4 rounded-3xl bg-white p-5 shadow-sm ring-1 ring-slate-100 md:max-w-2xl md:p-6"
    >
      <h2 class="text-lg font-extrabold text-slate-900">Subir material</h2>

      <label class="block">
        <span class="text-sm font-semibold text-slate-600">Materia y curso</span>
        <select v-model="materiaCurso" required class="campo">
          <option value="" disabled>Elegí una opción</option>
          <option v-for="m in misMaterias" :key="m.id" :value="m.id">
            {{ m.materia_nombre }} — {{ m.curso_nombre }}
          </option>
        </select>
      </label>
      <p v-if="errorAccion" role="alert" class="mt-4 rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-600">
        {{ errorAccion }}
      </p>
      <p v-if="!cargando && !misMaterias.length" class="text-sm font-semibold text-amber-600">
        No tenés materias asignadas todavía. Pedile al administrador que te asigne una.
      </p>

      <label class="block">
        <span class="text-sm font-semibold text-slate-600">Título</span>
        <input v-model="titulo" required maxlength="200" class="campo" placeholder="Ej: Guía de ejercicios 3" />
      </label>

      <label class="block">
        <span class="text-sm font-semibold text-slate-600">Descripción (opcional)</span>
        <textarea v-model="descripcion" rows="3" class="campo"></textarea>
      </label>

      <div>
        <span class="text-sm font-semibold text-slate-600">Archivo</span>
        <label
          class="mt-1 flex cursor-pointer flex-col items-center gap-1 rounded-2xl border-2 border-dashed border-blue-200 bg-blue-50/50 px-4 py-6 text-center transition hover:border-brand focus-within:ring-2 focus-within:ring-brand/30"
        >
          <AppIcon name="upload" class="size-7 text-brand" />
          <span class="text-sm font-bold break-all text-brand">
            {{ archivo ? archivo.name : 'Tocá para elegir un archivo' }}
          </span>
          <span class="text-xs text-slate-500">
            {{ archivo ? tamano : `PDF, Word, Excel, PowerPoint, imágenes o texto · hasta ${MAX_MB} MB` }}
          </span>
          <input ref="inputArchivo" type="file" :accept="aceptar" class="sr-only" @change="elegirArchivo" />
        </label>
      </div>

      <p v-if="errorForm" role="alert" class="rounded-lg bg-red-50 px-3 py-2 text-sm font-semibold text-red-600">
        {{ errorForm }}
      </p>
      <p v-if="exito" role="status" class="rounded-lg bg-green-50 px-3 py-2 text-sm font-semibold text-green-700">
        {{ exito }}
      </p>

      <button type="submit" :disabled="enviando || !misMaterias.length" class="boton-principal">
        {{ enviando ? 'Subiendo...' : 'Subir material' }}
      </button>
    </form>

    <!-- Listado: lo ven todos los roles -->
    <p v-if="cargando" class="mt-6 text-slate-500">Cargando...</p>
    <p v-else-if="error" class="mt-6 rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-600">{{ error }}</p>
    <p v-else-if="!materiales.length" class="mt-6 text-slate-500">Todavía no hay materiales.</p>
    <ul v-else class="mt-6 grid gap-3 md:grid-cols-2">
      <li
        v-for="m in materiales"
        :id="`material-${m.id}`"
        :key="m.id"
        class="flex flex-col rounded-2xl border bg-white p-4 shadow-sm transition"
        :class="[
          destacado === m.id ? 'border-brand ring-2 ring-brand/30' : 'border-blue-100',
          { 'md:col-span-2': abiertos[m.id] },
        ]"
      >
        <div class="flex items-start gap-3">
          <span class="grid size-11 shrink-0 place-items-center rounded-xl bg-blue-50 text-brand">
            <AppIcon name="document" class="size-6" />
          </span>
          <div class="min-w-0 flex-1">
            <h3 class="font-bold text-slate-900">{{ m.titulo }}</h3>
            <p class="text-xs font-semibold text-brand">{{ m.materia_nombre }} · {{ m.curso_nombre }}</p>
          </div>
        </div>

        <p v-if="m.descripcion" class="mt-2 text-sm whitespace-pre-line text-slate-500">{{ m.descripcion }}</p>
        <p class="mt-2 text-xs text-slate-400">
          {{ m.docente_nombre || 'Docente' }} · {{ fechaCorta(m.fecha_subida) }}
        </p>

        <div class="mt-auto flex items-center gap-2 pt-3">
          <button
            type="button"
            :disabled="descargando === m.id"
            @click="descargar(m)"
            class="flex min-w-0 flex-1 items-center justify-center gap-2 rounded-xl bg-blue-50 py-2 text-sm font-bold text-brand hover:bg-blue-100 disabled:opacity-60">
            <AppIcon name="download" class="size-5 shrink-0" />
            <span class="truncate">{{ descargando === m.id ? 'Descargando...' : m.archivo_nombre }}</span>
        </button>
          <button
            v-if="puedeSubir"
            type="button"
            @click="eliminar(m)"
            class="rounded-xl px-3 py-2 text-sm font-bold text-red-600 hover:bg-red-50"
          >
            Eliminar
          </button>
        </div>

        <button
          type="button"
          @click="alternarConsultas(m)"
          class="mt-3 flex items-center gap-2 text-sm font-bold text-brand"
        >
          <AppIcon name="chat" class="size-5" />
          {{ abiertos[m.id] ? 'Ocultar consultas' : `Consultas (${m.consultas_count})` }}
        </button>

        <ChatConsultas v-if="abiertos[m.id]" :material-id="m.id" @enviada="m.consultas_count++" />
      </li>
    </ul>
  </div>
</template>