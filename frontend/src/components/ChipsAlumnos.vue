<script setup>
import { useAlumnosStore } from '@/stores/alumnos'
import { nombreCompleto } from '@/utils/formato'

const alumnos = useAlumnosStore()
</script>

<template>
  <div v-if="alumnos.lista.length > 1" class="flex flex-wrap gap-2">
    <button
      v-for="a in alumnos.lista"
      :key="a.id"
      type="button"
      @click="alumnos.seleccionar(a.id)"
      class="rounded-full px-4 py-1.5 text-xs font-bold transition"
      :class="a.id === alumnos.seleccionadoId ? 'bg-brand text-white' : 'bg-slate-200/70 text-slate-600'"
    >
      {{ nombreCompleto(a) }}
    </button>
  </div>
</template>