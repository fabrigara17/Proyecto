import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || null)
  const usuario = ref(null)

  const estaAutenticado = computed(() => !!token.value)
  const rol = computed(() => usuario.value?.rol ?? null)
  const debeCambiarPassword = computed(() => usuario.value?.debe_cambiar_password ?? false)

  function setSesion(nuevoToken, datosUsuario) {
    token.value = nuevoToken
    usuario.value = datosUsuario
    localStorage.setItem('token', nuevoToken)
  }

  function setUsuario(datosUsuario) {
    usuario.value = datosUsuario
  }

  function actualizarTokenTrasPasswordCambiada(nuevoToken) {
    token.value = nuevoToken
    usuario.value = { ...usuario.value, debe_cambiar_password: false }
    localStorage.setItem('token', nuevoToken)
  }

  function cerrarSesion() {
    token.value = null
    usuario.value = null
    localStorage.removeItem('token')
  }

  return {
    token, usuario, estaAutenticado, rol, debeCambiarPassword,
    setSesion, setUsuario, actualizarTokenTrasPasswordCambiada, cerrarSesion,
  }
})