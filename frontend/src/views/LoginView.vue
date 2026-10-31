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
      <!-- Marca -->
      <div class="flex flex-col items-center md:items-start">
        <svg viewBox="0 0 96 96" class="size-16" aria-hidden="true">
          <rect x="12" y="8" width="72" height="80" rx="10" fill="#1b3a5c" />
          <rect x="24" y="22" width="48" height="34" rx="6" fill="#fff" />
          <path d="M36 54l-4 12 14-12z" fill="#fff" />
          <rect x="32" y="31" width="32" height="4" rx="2" fill="#1b3a5c" />
          <rect x="32" y="40" width="24" height="4" rx="2" fill="#1b3a5c" />
          <g fill="#8fa6bf">
            <circle cx="12" cy="24" r="4" /><circle cx="12" cy="38" r="4" />
            <circle cx="12" cy="52" r="4" /><circle cx="12" cy="66" r="4" />
          </g>
        </svg>

        <h1 class="mt-5 text-3xl font-semibold tracking-tight text-brand-dark">Libreta Digital</h1>
        <p class="mt-2 max-w-xs text-center text-slate-500 md:text-left">
          Comunicados, asistencias y calificaciones de la institución.
        </p>
      </div>

      <!-- Acceso -->
      <div class="mt-8 rounded-lg border border-slate-200 bg-white p-6 shadow-sm md:mt-0 md:p-8">
        <Transition
          mode="out-in"
          enter-active-class="transition duration-200 ease-out"
          enter-from-class="opacity-0 translate-y-1"
          leave-active-class="transition duration-100 ease-in"
          leave-to-class="opacity-0"
        >
          <form v-if="mostrarForm" @submit.prevent="handleSubmit" class="space-y-4">
            <h2 class="text-xl font-semibold text-slate-900">Iniciar sesión</h2>

            <label class="block">
              <span class="text-sm font-medium text-slate-600">Usuario</span>
              <input v-model="username" autocomplete="username" required class="campo" />
            </label>

            <label class="block">
              <span class="text-sm font-medium text-slate-600">Contraseña</span>
              <input v-model="password" type="password" autocomplete="current-password" required class="campo" />
            </label>

            <Transition
              enter-active-class="transition duration-200 ease-out"
              enter-from-class="opacity-0 -translate-y-1"
              leave-active-class="transition duration-150 ease-in"
              leave-to-class="opacity-0"
            >
              <p v-if="error" role="alert" class="rounded-md bg-red-50 px-3 py-2 text-sm font-medium text-red-600">
                {{ error }}
              </p>
            </Transition>

            <button type="submit" :disabled="cargando" class="boton-principal">
              {{ cargando ? 'Ingresando...' : 'Ingresar' }}
            </button>
          </form>

          <button v-else type="button" @click="mostrarForm = true" class="boton-principal">
            Iniciar sesión
          </button>
        </Transition>

        <button
          type="button"
          @click="mostrarAyuda = !mostrarAyuda"
          class="mt-4 block w-full text-center text-sm font-medium text-brand transition-colors hover:text-brand-dark hover:underline"
        >
          ¿Necesitás ayuda?
        </button>

        <Transition
          enter-active-class="transition duration-200 ease-out"
          enter-from-class="opacity-0 -translate-y-1"
          leave-active-class="transition duration-150 ease-in"
          leave-to-class="opacity-0"
        >
          <p v-if="mostrarAyuda" class="mt-2 rounded-md bg-blue-50 p-3 text-center text-sm text-slate-600">
            Tu usuario y tu contraseña inicial te los da la escuela. Si no los tenés o no podés ingresar,
            comunicate con la institución.
          </p>
        </Transition>
      </div>
    </div>
  </div>
</template>