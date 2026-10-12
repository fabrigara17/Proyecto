<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import api from '@/services/api' // ASUNCIÓN: instancia de axios con baseURL '/api' y el token; ajustá este import
import { crearUsuario } from '@/services/usuarios'
import { mensajeError } from '@/utils/errores'

const cursos = ref([])
const cursoId = ref(null)
const inscripciones = ref([])
const vinculos = ref([])
const cargando = ref(true)
const error = ref('')

const mostrarAlta = ref(false)
const formAlumno = ref(formVacio())
const guardando = ref(false)
const errorForm = ref('')
const creado = ref(null) // { username, password } para entregar

const activo = ref(null) // alumno con el panel de familiar abierto
const modo = ref('existente') // 'existente' | 'nuevo'
const q = ref('')
const resultados = ref([])
const parentesco = ref('')
const formFam = ref(formVacio())
const errorFam = ref('')

const mostrarExistente = ref(false)
const qAlumno = ref('')
const resultadosAlumnos = ref([])
const errorInscribir = ref('')

async function buscarAlumnos() {
  errorInscribir.value = ''
  try {
    const { data } = await api.get('/api/usuarios/', {
      params: { rol: 'ALUMNO', q: qAlumno.value.trim() },
    })
    const inscriptos = new Set(inscripciones.value.map((i) => i.alumno))
    resultadosAlumnos.value = (data.results ?? data).filter((a) => !inscriptos.has(a.id))
  } catch (e) {
    errorInscribir.value = mensajeError(e, 'No se pudo buscar.')
  }
}

async function inscribir(alumnoId) {
  errorInscribir.value = ''
  try {
    await api.post('/api/inscripciones/', { alumno: alumnoId, curso: cursoId.value })
    resultadosAlumnos.value = resultadosAlumnos.value.filter((a) => a.id !== alumnoId)
    await cargarCurso()
  } catch (e) {
    errorInscribir.value = mensajeError(e, 'No se pudo inscribir al alumno.')
  }
}

function formVacio() {
  return { username: '', first_name: '', last_name: '', password: '' }
}

const familiaresPorAlumno = computed(() => {
  const mapa = {}
  for (const v of vinculos.value) (mapa[v.alumno] ??= []).push(v)
  return mapa
})

onMounted(async () => {
  try {
    const { data } = await api.get('/api/cursos/mis-cursos/')
    cursos.value = data
    cursoId.value = data[0]?.id ?? null
  } catch (e) {
    error.value = mensajeError(e, 'No pudimos cargar tus cursos.')
  } finally {
    if (!cursoId.value) cargando.value = false
  }
})

watch(cursoId, cargarCurso)

async function cargarCurso() {
  if (!cursoId.value) return
  cargando.value = true
  error.value = ''
  activo.value = null
  try {
    const params = { curso: cursoId.value }
    const [ins, vin] = await Promise.all([
      api.get('/api/inscripciones/', { params }),
      api.get('/api/vinculos-familiares/', { params }),
    ])
    inscripciones.value = ins.data
    vinculos.value = vin.data
  } catch (e) {
    error.value = mensajeError(e, 'No pudimos cargar los alumnos del curso.')
  } finally {
    cargando.value = false
  }
}

function generarPassword(destino) {
  const letras = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789'
  const azar = crypto.getRandomValues(new Uint32Array(10))
  destino.password = Array.from(azar, (n) => letras[n % letras.length]).join('')
}

function datosUsuario(f, rol) {
  return {
    username: f.username.trim(),
    first_name: f.first_name.trim(),
    last_name: f.last_name.trim(),
    email: '',
    rol,
    password: f.password,
  }
}

// --- Alumno: alta + inscripción al curso seleccionado ---
async function crearAlumno() {
  guardando.value = true
  errorForm.value = ''
  const f = formAlumno.value
  try {
    const nuevo = await crearUsuario(datosUsuario(f, 'ALUMNO'))
    creado.value = { username: nuevo.username, password: f.password }
    try {
      await api.post('/api/inscripciones/', { alumno: nuevo.id, curso: cursoId.value })
    } catch (e) {
      errorForm.value = `El alumno se creó, pero no se pudo inscribir al curso: ${mensajeError(e, '')}`
    }
    formAlumno.value = formVacio()
    mostrarAlta.value = false
    await cargarCurso()
  } catch (e) {
    errorForm.value = mensajeError(e, 'No se pudo crear el alumno.')
  } finally {
    guardando.value = false
  }
}

async function quitarDelCurso(ins) {
  if (!confirm(`¿Quitar a ${ins.alumno_nombre} de este curso?`)) return
  try {
    await api.delete(`/api/inscripciones/${ins.id}/`)
    await cargarCurso()
  } catch (e) {
    error.value = mensajeError(e, 'No se pudo quitar al alumno del curso.')
  }
}

// --- Familiar ---
function abrirPanel(alumnoId) {
  activo.value = activo.value === alumnoId ? null : alumnoId
  modo.value = 'existente'
  q.value = ''
  resultados.value = []
  parentesco.value = ''
  formFam.value = formVacio()
  errorFam.value = ''
}

async function buscarFamilias() {
  errorFam.value = ''
  try {
    const { data } = await api.get('/api/usuarios/', { params: { rol: 'FAMILIA', q: q.value.trim() } })
    resultados.value = data.results ?? data
  } catch (e) {
    errorFam.value = mensajeError(e, 'No se pudo buscar.')
  }
}

async function vincular(tutorId) {
  await api.post('/api/vinculos-familiares/', {
    tutor: tutorId,
    alumno: activo.value,
    parentesco: parentesco.value.trim(),
  })
  activo.value = null
  await cargarCurso()
}

async function vincularExistente(tutorId) {
  errorFam.value = ''
  try {
    await vincular(tutorId)
  } catch (e) {
    errorFam.value = mensajeError(e, 'No se pudo vincular.')
  }
}

async function crearYVincular() {
  errorFam.value = ''
  const f = formFam.value
  try {
    const nuevo = await crearUsuario(datosUsuario(f, 'FAMILIA'))
    creado.value = { username: nuevo.username, password: f.password }
    await vincular(nuevo.id)
  } catch (e) {
    errorFam.value = mensajeError(e, 'No se pudo crear o vincular al familiar.')
  }
}

async function quitarVinculo(v) {
  if (!confirm(`¿Desvincular a ${v.tutor_nombre}?`)) return
  try {
    await api.delete(`/api/vinculos-familiares/${v.id}/`)
    await cargarCurso()
  } catch (e) {
    error.value = mensajeError(e, 'No se pudo desvincular.')
  }
}
</script>

<template>
  <div class="pagina">
    <div class="flex items-start justify-between gap-3">
      <div>
        <h1 class="titulo-pagina">Alumnos</h1>
        <p class="mt-1 text-sm text-slate-500">Alumnos de tus cursos y sus familiares.</p>
      </div>
      <div v-if="cursoId && !mostrarAlta" class="flex shrink-0 gap-2">
        <button type="button" @click="mostrarExistente = !mostrarExistente"
          class="rounded-xl bg-blue-50 px-4 font-bold text-brand hover:bg-blue-100">
          Inscribir existente
        </button>
        <button type="button" @click="mostrarAlta = true" class="boton-principal !w-auto px-4">
          Nuevo alumno
        </button>
      </div>
    </div>

    <select v-if="cursos.length" v-model="cursoId" class="campo mt-4 md:max-w-xs">
      <option v-for="c in cursos" :key="c.id" :value="c.id">{{ c.nombre }} ({{ c.anio_lectivo }})</option>
    </select>
    <p v-else-if="!cargando" class="mt-4 text-slate-500">No tenés cursos asignados.</p>

    <div v-if="creado" role="status" class="mt-4 rounded-2xl border border-green-200 bg-green-50 p-4 md:max-w-xl">
      <p class="font-bold text-green-800">Usuario creado</p>
      <p class="mt-1 text-sm text-green-800">Esta contraseña solo se muestra ahora. Se pedirá cambiarla al primer ingreso.</p>
      <p class="mt-3 font-mono text-sm text-slate-900">
        Usuario: <strong>{{ creado.username }}</strong><br />
        Contraseña: <strong>{{ creado.password }}</strong>
      </p>
      <button type="button" @click="creado = null" class="mt-3 text-sm font-bold text-brand">Cerrar</button>
    </div>

    <!-- Inscribir un alumno que ya existe -->
    <div v-if="mostrarExistente" class="mt-4 grid gap-3 rounded-2xl border border-blue-100 bg-white p-4 shadow-sm md:max-w-xl">
      <h2 class="font-bold text-slate-900">Inscribir alumno existente</h2>
      <form @submit.prevent="buscarAlumnos" class="flex gap-2">
        <input v-model="qAlumno" type="search" placeholder="Buscar por nombre o usuario" class="campo" />
        <button type="submit" class="shrink-0 rounded-xl bg-blue-50 px-3 text-sm font-bold text-brand">Buscar</button>
      </form>
      <ul class="grid gap-1">
        <li v-for="a in resultadosAlumnos" :key="a.id" class="flex items-center justify-between gap-2 text-sm">
          <span class="truncate">{{ a.first_name }} {{ a.last_name }} <span class="text-slate-400">({{ a.username }})</span></span>
          <button type="button" @click="inscribir(a.id)" class="shrink-0 font-bold text-brand">Inscribir</button>
        </li>
      </ul>
      <p v-if="errorInscribir" role="alert" class="rounded-xl bg-red-50 p-2 text-sm font-semibold text-red-600">{{ errorInscribir }}</p>
    </div>

    <!-- Alta de alumno -->
    <form v-if="mostrarAlta" @submit.prevent="crearAlumno"
      class="mt-4 grid gap-3 rounded-2xl border border-blue-100 bg-white p-4 shadow-sm md:max-w-xl">
      <h2 class="font-bold text-slate-900">Nuevo alumno</h2>
      <label class="block">
        <span class="text-sm font-semibold text-slate-600">Usuario *</span>
        <input v-model="formAlumno.username" required maxlength="150" autocomplete="off" class="campo" />
      </label>
      <div class="grid gap-3 sm:grid-cols-2">
        <label class="block">
          <span class="text-sm font-semibold text-slate-600">Nombre</span>
          <input v-model="formAlumno.first_name" maxlength="150" class="campo" />
        </label>
        <label class="block">
          <span class="text-sm font-semibold text-slate-600">Apellido</span>
          <input v-model="formAlumno.last_name" maxlength="150" class="campo" />
        </label>
      </div>
      <label class="block">
        <span class="text-sm font-semibold text-slate-600">Contraseña inicial *</span>
        <div class="flex gap-2">
          <input v-model="formAlumno.password" required minlength="8" autocomplete="off" class="campo" />
          <button type="button" @click="generarPassword(formAlumno)"
            class="shrink-0 rounded-xl bg-blue-50 px-3 text-sm font-bold text-brand hover:bg-blue-100">Generar</button>
        </div>
      </label>
      <p v-if="errorForm" role="alert" class="rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-600">{{ errorForm }}</p>
      <div class="flex gap-3">
        <button type="submit" :disabled="guardando" class="boton-principal">{{ guardando ? 'Creando...' : 'Crear e inscribir' }}</button>
        <button type="button" @click="mostrarAlta = false; errorForm = ''"
          class="rounded-xl px-4 font-bold text-slate-500 hover:bg-slate-100">Cancelar</button>
      </div>
    </form>

    <p v-if="cargando && cursoId" class="mt-6 text-slate-500">Cargando...</p>
    <p v-else-if="error" role="alert" class="mt-6 rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-600">{{ error }}</p>
    <p v-else-if="cursoId && !inscripciones.length" class="mt-6 text-slate-500">Este curso todavía no tiene alumnos.</p>

    <ul v-else class="mt-5 grid gap-3 md:grid-cols-2">
      <li v-for="i in inscripciones" :key="i.id" class="rounded-2xl border border-blue-100 bg-white p-4 shadow-sm">
        <div class="flex items-start justify-between gap-3">
          <p class="font-bold text-slate-900">{{ i.alumno_nombre }}</p>
          <button type="button" @click="quitarDelCurso(i)" class="text-xs font-bold text-red-600">Quitar del curso</button>
        </div>

        <ul class="mt-2 grid gap-1">
          <li v-for="v in familiaresPorAlumno[i.alumno] || []" :key="v.id"
            class="flex items-center justify-between gap-2 rounded-lg bg-slate-50 px-2 py-1 text-sm">
            <span class="truncate">{{ v.tutor_nombre }}<span v-if="v.parentesco" class="text-slate-500"> · {{ v.parentesco }}</span></span>
            <button type="button" @click="quitarVinculo(v)" class="shrink-0 text-xs font-bold text-red-600">Desvincular</button>
          </li>
          <li v-if="!(familiaresPorAlumno[i.alumno] || []).length" class="text-xs text-amber-600">Sin familiares vinculados</li>
        </ul>

        <button type="button" @click="abrirPanel(i.alumno)" class="mt-3 text-sm font-bold text-brand">
          {{ activo === i.alumno ? 'Cerrar' : 'Agregar familiar' }}
        </button>

        <div v-if="activo === i.alumno" class="mt-3 grid gap-3 border-t border-slate-100 pt-3">
          <div class="flex gap-2 text-sm font-bold">
            <button type="button" @click="modo = 'existente'" :class="modo === 'existente' ? 'text-brand' : 'text-slate-400'">Existente</button>
            <button type="button" @click="modo = 'nuevo'" :class="modo === 'nuevo' ? 'text-brand' : 'text-slate-400'">Nuevo</button>
          </div>

          <input v-model="parentesco" maxlength="30" placeholder="Parentesco (madre, padre, tutor...)" class="campo" />

          <template v-if="modo === 'existente'">
            <form @submit.prevent="buscarFamilias" class="flex gap-2">
              <input v-model="q" type="search" placeholder="Buscar por nombre o usuario" class="campo" />
              <button type="submit" class="shrink-0 rounded-xl bg-blue-50 px-3 text-sm font-bold text-brand">Buscar</button>
            </form>
            <ul class="grid gap-1">
              <li v-for="f in resultados" :key="f.id" class="flex items-center justify-between gap-2 text-sm">
                <span class="truncate">{{ f.first_name }} {{ f.last_name }} <span class="text-slate-400">({{ f.username }})</span></span>
                <button type="button" @click="vincularExistente(f.id)" class="shrink-0 font-bold text-brand">Vincular</button>
              </li>
            </ul>
          </template>

          <form v-else @submit.prevent="crearYVincular" class="grid gap-2">
            <input v-model="formFam.username" required maxlength="150" placeholder="Usuario *" autocomplete="off" class="campo" />
            <div class="grid gap-2 sm:grid-cols-2">
              <input v-model="formFam.first_name" maxlength="150" placeholder="Nombre" class="campo" />
              <input v-model="formFam.last_name" maxlength="150" placeholder="Apellido" class="campo" />
            </div>
            <div class="flex gap-2">
              <input v-model="formFam.password" required minlength="8" placeholder="Contraseña inicial *" autocomplete="off" class="campo" />
              <button type="button" @click="generarPassword(formFam)"
                class="shrink-0 rounded-xl bg-blue-50 px-3 text-sm font-bold text-brand">Generar</button>
            </div>
            <button type="submit" class="boton-principal">Crear y vincular</button>
          </form>

          <p v-if="errorFam" role="alert" class="rounded-xl bg-red-50 p-2 text-sm font-semibold text-red-600">{{ errorFam }}</p>
        </div>
      </li>
    </ul>
  </div>
</template>