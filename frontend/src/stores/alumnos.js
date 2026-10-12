import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getMisAlumnos } from '@/services/alumnos'

export const useAlumnosStore = defineStore('alumnos', () => {
  const lista = ref([])
  const seleccionadoId = ref(null)
  const cargado = ref(false)

  const seleccionado = computed(
    () => lista.value.find((a) => a.id === seleccionadoId.value) ?? null,
  )

  async function cargar(rol) {
    if (cargado.value) return
    if (rol === 'FAMILIA') {
      lista.value = await getMisAlumnos()
      seleccionadoId.value = lista.value[0]?.id ?? null
    }
    cargado.value = true
  }

  function seleccionar(id) {
    seleccionadoId.value = id
  }

  function reset() {
    lista.value = []
    seleccionadoId.value = null
    cargado.value = false
  }

  return { lista, seleccionadoId, seleccionado, cargar, seleccionar, reset }
})