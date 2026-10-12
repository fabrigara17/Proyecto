<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { login } from '@/services/auth'
import { useAuthStore } from '@/stores/auth'

const username = ref('')
const password = ref('')
const error = ref('')
const cargando = ref(false)
const mostrarForm = ref(false)
const mostrarAyuda = ref(false)
const router = useRouter()
const auth = useAuthStore()

async function handleSubmit() {
  error.value = ''
  cargando.value = true
  try {
    const { token, usuario } = await login(username.value.trim(), password.value)
    auth.setSesion(token, usuario)
    router.push('/') // el router lo manda a cambiar contraseña si hace falta
  } catch (e) {
    if (!e.response) {
      error.value = 'No se pudo conectar con el servidor. Probá de nuevo en un momento.'
    } else if (e.response.status === 429) {
      error.value = 'Demasiados intentos. Esperá un minuto y probá de nuevo.'
    } else {
      error.value = 'Usuario o contraseña incorrectos'
    }
  } finally {
    cargando.value = false
  }
}
</script>

<template>
  <div class="grid min-h-dvh place-items-center px-6 py-10">
    <div class="w-full max-w-sm md:grid md:max-w-4xl md:grid-cols-2 md:items-center md:gap-14">
      <!-- Marca + ilustración -->
      <div class="flex flex-col items-center">
        <svg viewBox="0 0 96 96" class="size-24" aria-hidden="true">
          <rect x="12" y="8" width="72" height="80" rx="14" fill="#1565c0" />
          <rect x="24" y="22" width="48" height="34" rx="10" fill="#fff" />
          <path d="M36 54l-4 12 14-12z" fill="#fff" />
          <rect x="32" y="31" width="32" height="4" rx="2" fill="#1565c0" />
          <rect x="32" y="40" width="24" height="4" rx="2" fill="#1565c0" />
          <g fill="#90caf9">
            <circle cx="12" cy="24" r="4" /><circle cx="12" cy="38" r="4" />
            <circle cx="12" cy="52" r="4" /><circle cx="12" cy="66" r="4" />
          </g>
        </svg>

        <h1 class="mt-6 text-4xl font-extrabold text-brand-dark">Libreta Digital</h1>

        <div class="mt-10 grid h-44 w-full place-items-center rounded-3xl bg-linear-to-br from-blue-50 to-blue-200 md:mt-8">
          <svg viewBox="0 0 220 110" class="h-28" aria-hidden="true">
            <rect x="30" y="14" width="52" height="82" rx="10" fill="#fff" />
            <rect x="38" y="30" width="28" height="5" rx="2.5" fill="#90caf9" />
            <rect x="38" y="42" width="36" height="4" rx="2" fill="#cfd8dc" />
            <rect x="38" y="52" width="30" height="4" rx="2" fill="#cfd8dc" />
            <rect x="38" y="66" width="36" height="16" rx="8" fill="#dbe7fb" />
            <circle cx="82" cy="18" r="11" fill="#ef4444" />
            <text x="82" y="23" text-anchor="middle" font-size="13" font-weight="700" fill="#fff">2</text>
            <path d="M124 46l32-22 32 22z" fill="#5c85c4" />
            <rect x="128" y="46" width="56" height="50" fill="#7ea3d9" />
            <rect x="136" y="56" width="10" height="10" fill="#fff" />
            <rect x="151" y="56" width="10" height="10" fill="#fff" />
            <rect x="166" y="56" width="10" height="10" fill="#fff" />
            <rect x="150" y="74" width="12" height="22" fill="#5c85c4" />
          </svg>
        </div>
      </div>

      <!-- Acceso -->
      <div class="mt-10 md:mt-0">
        <form v-if="mostrarForm" @submit.prevent="handleSubmit" class="space-y-4">
          <h2 class="text-xl font-extrabold text-slate-900">Iniciar sesión</h2>

          <label class="block">
            <span class="text-sm font-semibold text-slate-600">Usuario</span>
            <input v-model="username" autocomplete="username" required class="campo" />
          </label>

          <label class="block">
            <span class="text-sm font-semibold text-slate-600">Contraseña</span>
            <input v-model="password" type="password" autocomplete="current-password" required class="campo" />
          </label>

          <p v-if="error" role="alert" class="rounded-lg bg-red-50 px-3 py-2 text-sm font-semibold text-red-600">
            {{ error }}
          </p>

          <button type="submit" :disabled="cargando" class="boton-principal">
            {{ cargando ? 'Ingresando...' : 'Ingresar' }}
          </button>
        </form>

        <button v-else type="button" @click="mostrarForm = true" class="boton-principal">
          Iniciar sesión
        </button>

        <button
          type="button"
          @click="mostrarAyuda = !mostrarAyuda"
          class="mt-4 block w-full text-center text-sm font-semibold text-brand"
        >
          ¿Necesitás ayuda?
        </button>
        <p v-if="mostrarAyuda" class="mt-2 rounded-xl bg-blue-50 p-3 text-center text-sm text-slate-600">
          Tu usuario y tu contraseña inicial te los da la escuela. Si no los tenés o no podés ingresar,
          comunicate con la institución.
        </p>
      </div>
    </div>
  </div>
</template>