<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getNotificaciones, marcarLeida, marcarTodasLeidas } from '@/services/notificaciones'
import { fechaHora } from '@/utils/formato'

const router = useRouter()

const notificaciones = ref([])
const cargando = ref(true)
const error = ref('')
const errorAccion = ref('')

const sinLeer = computed(() => notificaciones.value.filter((n) => !n.leida).length)

// Los avisos de material y de consultas llevan a la pantalla de Materiales
const tieneDestino = (n) => ['MATERIAL', 'CONSULTA'].includes(n.tipo) && !!n.referencia_id

onMounted(async () => {
  try {
    notificaciones.value = await getNotificaciones()
  } catch {
    error.value = 'No pudimos cargar los avisos. Probá de nuevo en un momento.'
  } finally {
    cargando.value = false
  }
})

async function abrir(n) {
  errorAccion.value = ''
  if (!n.leida) {
    try {
      await marcarLeida(n.id)
      n.leida = true
    } catch {
      if (!tieneDestino(n)) errorAccion.value = 'No se pudo marcar como leído. Probá de nuevo.'
    }
  }
  if (tieneDestino(n)) {
    router.push({ name: 'materiales', query: { material: n.referencia_id } })
  }
}

async function leerTodas() {
  errorAccion.value = ''
  try {
    await marcarTodasLeidas()
    notificaciones.value.forEach((n) => (n.leida = true))
  } catch {
    errorAccion.value = 'No se pudo actualizar. Probá de nuevo.'
  }
}
</script>

<template>
  <div class="pagina">
    <div class="flex items-center justify-between gap-3">
      <h1 class="titulo-pagina">Avisos</h1>
      <button v-if="sinLeer" type="button" @click="leerTodas" class="text-sm font-bold text-brand">
        Marcar todas como leídas
      </button>
    </div>

    <p v-if="errorAccion" role="alert" class="mt-3 rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-600">
      {{ errorAccion }}
    </p>

    <p v-if="cargando" class="mt-6 text-slate-500">Cargando...</p>
    <p v-else-if="error" class="mt-6 rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-600">{{ error }}</p>
    <p v-else-if="!notificaciones.length" class="mt-6 text-slate-500">No tenés avisos.</p>
    <ul v-else class="mt-5 grid gap-2 md:max-w-2xl">
      <li v-for="n in notificaciones" :key="n.id">
        <button
          type="button"
          @click="abrir(n)"
          class="flex w-full items-start gap-3 rounded-2xl border p-4 text-left shadow-sm transition"
          :class="n.leida ? 'border-slate-100 bg-white' : 'border-blue-200 bg-blue-50'"
        >
          <span
            class="mt-1.5 size-2.5 shrink-0 rounded-full"
            :class="n.leida ? 'bg-transparent' : 'bg-red-500'"
          ></span>
          <span class="flex-1">
            <span class="block text-sm font-semibold text-slate-800">{{ n.mensaje }}</span>
            <span class="block text-xs text-slate-400">{{ fechaHora(n.fecha_creacion) }}</span>
            <span v-if="tieneDestino(n)" class="mt-1 block text-xs font-bold text-brand">Ver en Materiales →</span>
          </span>
        </button>
      </li>
    </ul>
  </div>
</template>