import { ref } from 'vue'

const abierto = ref(false)

export function useMenuLateral() {
  return {
    abierto,
    abrir: () => (abierto.value = true),
    cerrar: () => (abierto.value = false),
    alternar: () => (abierto.value = !abierto.value),
  }
}