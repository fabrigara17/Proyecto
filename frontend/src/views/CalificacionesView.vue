<script setup>
import { onMounted, ref } from 'vue'
import { getCalificaciones } from '@/services/calificaciones'

const calificaciones = ref([])
const cargando = ref(true)

onMounted(async () => {
  calificaciones.value = await getCalificaciones()
  cargando.value = false
})
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-slate-800 mb-4">Calificaciones</h1>
    <p v-if="cargando" class="text-slate-500">Cargando...</p>
    <p v-else-if="!calificaciones.length" class="text-slate-500">No hay calificaciones cargadas todavía.</p>
    <div v-else class="bg-white rounded-lg shadow overflow-hidden">
      <table class="w-full text-left text-sm">
        <thead class="bg-slate-100 text-slate-600">
          <tr>
            <th class="px-4 py-2">Alumno</th>
            <th class="px-4 py-2">Materia</th>
            <th class="px-4 py-2">Nota</th>
            <th class="px-4 py-2">Fecha</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in calificaciones" :key="c.id" class="border-t border-slate-100">
            <td class="px-4 py-2">{{ c.alumno }}</td>
            <td class="px-4 py-2">{{ c.materia }}</td>
            <td class="px-4 py-2 font-semibold">{{ c.nota }}</td>
            <td class="px-4 py-2 text-slate-500">{{ c.fecha }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>