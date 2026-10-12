<script setup>
import { computed, onMounted, ref } from 'vue'
import { crearUsuario, getUsuarios } from '@/services/usuarios'
import { mensajeError } from '@/utils/errores'
import { nombreCompleto } from '@/utils/formato'
import { haceCuanto, normalizar } from '@/utils/texto'

// De mayor a menor cargo
const CARGOS = [
  { rol: 'CONDUCCION', titulo: 'Equipo de Conducción' },
  { rol: 'PRECEPTOR', titulo: 'Preceptores' },
  { rol: 'DOCENTE', titulo: 'Docentes' },
]
const ROLES_DEL_EQUIPO = CARGOS.map((c) => c.rol)
const NOMBRE_ROL = { CONDUCCION: 'Equipo de Conducción', PRECEPTOR: 'Preceptor', DOCENTE: 'Docente' }

function formVacio() {
  return { username: '', first_name: '', last_name: '', email: '', rol: '', password: '' }
}

const usuarios = ref([])
const cargando = ref(true)
const errorLista = ref('')
const busqueda = ref('')

const mostrarForm = ref(false)
const form = ref(formVacio())
const guardando = ref(false)
const errorForm = ref('')
const creado = ref(null) // { username, password }: datos para entregar a la persona
const copiado = ref(false)

// Solo el equipo: el rol de desarrollo recibe también alumnos y familias, que acá no van
const equipo = computed(() => usuarios.value.filter((u) => ROLES_DEL_EQUIPO.includes(u.rol)))

const grupos = computed(() => {
  const q = normalizar(busqueda.value.trim())
  const visibles = q
    ? equipo.value.filter((u) => normalizar(`${u.username} ${u.first_name} ${u.last_name}`).includes(q))
    : equipo.value
  return CARGOS
    .map((c) => ({ ...c, miembros: visibles.filter((u) => u.rol === c.rol) }))
    .filter((g) => g.miembros.length)
})

async function cargar() {
  errorLista.value = ''
  try {
    usuarios.value = await getUsuarios()
  } catch (e) {
    errorLista.value = mensajeError(e, 'No pudimos cargar el equipo. Probá de nuevo.')
  } finally {
    cargando.value = false
  }
}

onMounted(cargar)

function abrirForm() {
  creado.value = null
  errorForm.value = ''
  mostrarForm.value = true
}

function cancelar() {
  mostrarForm.value = false
  form.value = formVacio()
  errorForm.value = ''
}

// Contraseña temporal sin caracteres que se confundan (0/O, 1/l/I)
function generarPassword() {
  const letras = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789'
  const azar = crypto.getRandomValues(new Uint32Array(10))
  form.value.password = Array.from(azar, (n) => letras[n % letras.length]).join('')
}

async function enviar() {
  errorForm.value = ''
  guardando.value = true
  try {
    const f = form.value
    const nuevo = await crearUsuario({
      username: f.username.trim(),
      first_name: f.first_name.trim(),
      last_name: f.last_name.trim(),
      email: f.email.trim(),
      rol: f.rol,
      password: f.password,
    })
    creado.value = { username: nuevo.username, password: f.password }
    copiado.value = false
    form.value = formVacio()
    mostrarForm.value = false
    await cargar()
  } catch (e) {
    errorForm.value = mensajeError(e, 'No se pudo crear el usuario.')
  } finally {
    guardando.value = false
  }
}

async function copiar() {
  const texto = `Usuario: ${creado.value.username}\nContraseña: ${creado.value.password}`
  try {
    await navigator.clipboard.writeText(texto)
    copiado.value = true
    setTimeout(() => (copiado.value = false), 2000)
  } catch {
    // Sin permiso del navegador: se puede copiar a mano desde pantalla
  }
}
</script>

<template>
  <div class="pagina">
    <div class="flex items-start justify-between gap-3">
      <div>
        <h1 class="titulo-pagina">Equipo</h1>
        <p class="mt-1 text-sm text-slate-500">Conducción, preceptores y docentes de la escuela.</p>
      </div>
      <button v-if="!mostrarForm" type="button" @click="abrirForm" class="boton-principal !w-auto shrink-0 px-4">
        Nuevo integrante
      </button>
    </div>

    <!-- Datos para entregar a quien se acaba de crear -->
    <div v-if="creado" role="status" class="mt-4 rounded-2xl border border-green-200 bg-green-50 p-4 md:max-w-xl">
      <p class="font-bold text-green-800">Usuario creado</p>
      <p class="mt-1 text-sm text-green-800">
        Entregale estos datos. Al ingresar por primera vez la app le va a pedir que cambie la contraseña.
        Esta contraseña solo se muestra ahora.
      </p>
      <p class="mt-3 font-mono text-sm text-slate-900">
        Usuario: <strong>{{ creado.username }}</strong><br />
        Contraseña: <strong>{{ creado.password }}</strong>
      </p>
      <div class="mt-3 flex gap-4 text-sm font-bold text-brand">
        <button type="button" @click="copiar">{{ copiado ? '¡Copiado!' : 'Copiar datos' }}</button>
        <button type="button" @click="creado = null">Cerrar</button>
      </div>
    </div>

    <!-- Alta -->
    <form
      v-if="mostrarForm"
      @submit.prevent="enviar"
      class="mt-4 grid gap-3 rounded-2xl border border-blue-100 bg-white p-4 shadow-sm md:max-w-xl"
    >
      <h2 class="font-bold text-slate-900">Nuevo integrante</h2>

      <label class="block">
        <span class="text-sm font-semibold text-slate-600">Usuario *</span>
        <input v-model="form.username" required maxlength="150" autocomplete="off" class="campo" />
        <span class="text-xs text-slate-400">Letras, números y @ . + - _ (sin espacios)</span>
      </label>

      <div class="grid gap-3 sm:grid-cols-2">
        <label class="block">
          <span class="text-sm font-semibold text-slate-600">Nombre</span>
          <input v-model="form.first_name" maxlength="150" class="campo" />
        </label>
        <label class="block">
          <span class="text-sm font-semibold text-slate-600">Apellido</span>
          <input v-model="form.last_name" maxlength="150" class="campo" />
        </label>
      </div>

      <label class="block">
        <span class="text-sm font-semibold text-slate-600">Email (opcional)</span>
        <input v-model="form.email" type="email" class="campo" />
      </label>

      <label class="block">
        <span class="text-sm font-semibold text-slate-600">Cargo *</span>
        <select v-model="form.rol" required class="campo">
          <option value="" disabled>Elegí un cargo</option>
          <option v-for="c in CARGOS" :key="c.rol" :value="c.rol">{{ NOMBRE_ROL[c.rol] }}</option>
        </select>
      </label>

      <label class="block">
        <span class="text-sm font-semibold text-slate-600">Contraseña inicial *</span>
        <div class="flex gap-2">
          <input v-model="form.password" required minlength="8" autocomplete="off" class="campo" />
          <button
            type="button"
            @click="generarPassword"
            class="shrink-0 rounded-xl bg-blue-50 px-3 text-sm font-bold text-brand hover:bg-blue-100"
          >
            Generar
          </button>
        </div>
        <span class="text-xs text-slate-400">Mínimo 8 caracteres. La persona va a tener que cambiarla al ingresar.</span>
      </label>

      <p v-if="errorForm" role="alert" class="rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-600">
        {{ errorForm }}
      </p>

      <div class="flex gap-3">
        <button type="submit" :disabled="guardando" class="boton-principal">
          {{ guardando ? 'Creando...' : 'Crear usuario' }}
        </button>
        <button type="button" @click="cancelar" class="rounded-xl px-4 font-bold text-slate-500 hover:bg-slate-100">
          Cancelar
        </button>
      </div>
    </form>

    <input v-model="busqueda" type="search" placeholder="Buscar por nombre o usuario" class="campo mt-6 md:max-w-sm" />

    <p v-if="cargando" class="mt-6 text-slate-500">Cargando...</p>
    <p v-else-if="errorLista" role="alert" class="mt-6 rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-600">
      {{ errorLista }}
    </p>
    <p v-else-if="!grupos.length" class="mt-6 text-slate-500">No hay integrantes para mostrar.</p>

    <template v-else>
      <section v-for="g in grupos" :key="g.rol" class="mt-6">
        <h2 class="text-sm font-bold uppercase tracking-wide text-slate-500">
          {{ g.titulo }} ({{ g.miembros.length }})
        </h2>
        <ul class="mt-2 grid gap-2 md:grid-cols-2">
          <li
            v-for="u in g.miembros"
            :key="u.id"
            class="flex items-center justify-between gap-3 rounded-2xl border border-blue-100 bg-white p-3 shadow-sm"
          >
            <div class="min-w-0">
              <p class="truncate font-bold text-slate-900">{{ nombreCompleto(u) }}</p>
              <p class="truncate text-xs text-slate-500">{{ u.username }}</p>
            </div>
            <div class="shrink-0 text-right">
              <p class="text-[10px] font-bold uppercase tracking-wide text-slate-400">Última conexión</p>
              <p class="text-xs font-semibold" :class="u.ultima_conexion ? 'text-slate-700' : 'text-amber-600'">
                {{ haceCuanto(u.ultima_conexion) }}
              </p>
              <span
                v-if="!u.is_active"
                class="mt-1 inline-block rounded-full bg-slate-200 px-2 py-0.5 text-xs font-bold text-slate-600"
              >
                Inactivo
              </span>
            </div>
          </li>
        </ul>
      </section>
    </template>
  </div>
</template>