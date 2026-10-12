<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { cambiarPassword } from '@/services/auth'
import { useAuthStore } from '@/stores/auth'

const passwordActual = ref('')
const passwordNueva = ref('')
const passwordRepetida = ref('')
const error = ref('')
const cargando = ref(false)
const auth = useAuthStore()
const router = useRouter()

async function handleSubmit() {
  error.value = ''
  if (passwordNueva.value !== passwordRepetida.value) {
    error.value = 'Las contraseñas nuevas no coinciden'
    return
  }
  cargando.value = true
  try {
    const { token } = await cambiarPassword(passwordActual.value, passwordNueva.value)
    auth.actualizarTokenTrasPasswordCambiada(token)
    router.push('/')
  } catch (e) {
    const data = e.response?.data
    error.value = data && typeof data === 'object'
      ? Object.values(data).flat().join(' ')
      : 'No se pudo cambiar la contraseña'
  } finally {
    cargando.value = false
  }
}
</script>

<template>
  <div class="grid min-h-dvh place-items-center px-6 py-10">
    <form
      @submit.prevent="handleSubmit"
      class="w-full max-w-md space-y-4 rounded-3xl bg-white p-6 shadow-sm ring-1 ring-slate-100 md:p-8"
    >
      <h1 class="text-2xl font-extrabold text-slate-900">Cambiar contraseña</h1>
      <p class="text-sm text-slate-500">
        Es tu primer inicio de sesión, tenés que definir una contraseña nueva para continuar.
      </p>

      <label class="block">
        <span class="text-sm font-semibold text-slate-600">Contraseña actual</span>
        <input v-model="passwordActual" type="password" autocomplete="current-password" required class="campo" />
      </label>

      <label class="block">
        <span class="text-sm font-semibold text-slate-600">Contraseña nueva</span>
        <input v-model="passwordNueva" type="password" autocomplete="new-password" required class="campo" />
      </label>

      <label class="block">
        <span class="text-sm font-semibold text-slate-600">Repetí la contraseña nueva</span>
        <input v-model="passwordRepetida" type="password" autocomplete="new-password" required class="campo" />
      </label>

      <p v-if="error" role="alert" class="rounded-lg bg-red-50 px-3 py-2 text-sm font-semibold text-red-600">
        {{ error }}
      </p>

      <button type="submit" :disabled="cargando" class="boton-principal">
        {{ cargando ? 'Guardando...' : 'Confirmar' }}
      </button>
    </form>
  </div>
</template>