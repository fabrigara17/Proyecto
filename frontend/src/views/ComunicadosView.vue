<script setup>
import { computed, onMounted, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import {
  crearComunicacion, eliminarComunicacion, getComunicaciones, getVistas, marcarVistas,
} from '@/services/comunicaciones'
import { mensajeError } from '@/utils/errores'
import { fechaHora, TIPOS_COMUNICADO } from '@/utils/formato'
import ComunicadoCard from '@/components/ComunicadoCard.vue'

const auth = useAuthStore()
const esAdmin = computed(() => auth.rol === 'ADMIN')

const comunicaciones = ref([])
const cargando = ref(true)
const error = ref('')

// Solo administrador
const mostrarForm = ref(false)
const form = ref({ titulo: '', tipo: 'AVISO', contenido: '' })
const publicando = ref(false)
const errorForm = ref('')
const errorAccion = ref('')
const abierto = ref(null) // comunicado con el detalle de lecturas desplegado
const vistas = ref(null)
const cargandoVistas = ref(false)

async function cargar() {
  error.value = ''
  try {
    comunicaciones.value = await getComunicaciones()
  } catch {
    error.value = 'No pudimos cargar los comunicados. Probá de nuevo en un momento.'
  } finally {
    cargando.value = false
  }
}

onMounted(async () => {
  await cargar()
  // Quien abre esta pantalla ve los comunicados completos: se registran como vistos
  if (!esAdmin.value) {
    const pendientes = comunicaciones.value.filter((c) => c.visto === false).map((c) => c.id)
    if (pendientes.length) {
      try {
        await marcarVistas(pendientes)
      } catch {
        // No es importante para quien está leyendo
      }
    }
  }
})

async function publicar() {
  publicando.value = true
  errorForm.value = ''
  try {
    await crearComunicacion({
      titulo: form.value.titulo.trim(),
      tipo: form.value.tipo,
      contenido: form.value.contenido.trim(),
    })
    form.value = { titulo: '', tipo: 'AVISO', contenido: '' }
    mostrarForm.value = false
    await cargar()
  } catch (e) {
    errorForm.value = mensajeError(e, 'No se pudo publicar el comunicado.')
  } finally {
    publicando.value = false
  }
}

async function eliminar(c) {
  if (!window.confirm(`¿Eliminar el comunicado "${c.titulo}"?`)) return
  errorAccion.value = ''
  try {
    await eliminarComunicacion(c.id)
    if (abierto.value === c.id) abierto.value = null
    await cargar()
  } catch (e) {
    errorAccion.value = mensajeError(e, 'No se pudo eliminar el comunicado.')
  }
}

async function alternarVistas(c) {
  if (abierto.value === c.id) {
    abierto.value = null
    return
  }
  abierto.value = c.id
  vistas.value = null
  cargandoVistas.value = true
  errorAccion.value = ''
  try {
    vistas.value = await getVistas(c.id)
  } catch (e) {
    errorAccion.value = mensajeError(e, 'No pudimos cargar quién lo vio.')
  } finally {
    cargandoVistas.value = false
  }
}
</script>

<template>
  <div class="pagina">
    <div class="flex items-start justify-between gap-3">
      <h1 class="titulo-pagina">Comunicados</h1>
      <button
        v-if="esAdmin && !mostrarForm"
        type="button"
        @click="mostrarForm = true"
        class="boton-principal !w-auto shrink-0 px-4"
      >
        Nuevo comunicado
      </button>
    </div>

    <!-- Publicar (administrador) -->
    <form
      v-if="esAdmin && mostrarForm"
      @submit.prevent="publicar"
      class="mt-4 grid gap-3 rounded-2xl border border-blue-100 bg-white p-4 shadow-sm md:max-w-xl"
    >
      <h2 class="font-bold text-slate-900">Nuevo comunicado</h2>
      <label class="block">
        <span class="text-sm font-semibold text-slate-600">Título *</span>
        <input v-model="form.titulo" required maxlength="200" class="campo" />
      </label>
      <label class="block">
        <span class="text-sm font-semibold text-slate-600">Tipo</span>
        <select v-model="form.tipo" class="campo">
          <option v-for="(texto, valor) in TIPOS_COMUNICADO" :key="valor" :value="valor">{{ texto }}</option>
        </select>
      </label>
      <label class="block">
        <span class="text-sm font-semibold text-slate-600">Contenido *</span>
        <textarea v-model="form.contenido" required rows="5" class="campo"></textarea>
      </label>

      <p v-if="errorForm" role="alert" class="rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-600">
        {{ errorForm }}
      </p>

      <div class="flex gap-3">
        <button type="submit" :disabled="publicando" class="boton-principal">
          {{ publicando ? 'Publicando...' : 'Publicar' }}
        </button>
        <button type="button" @click="mostrarForm = false" class="rounded-xl px-4 font-bold text-slate-500 hover:bg-slate-100">
          Cancelar
        </button>
      </div>
    </form>

    <p v-if="errorAccion" role="alert" class="mt-4 rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-600">
      {{ errorAccion }}
    </p>

    <p v-if="cargando" class="mt-6 text-slate-500">Cargando...</p>
    <p v-else-if="error" class="mt-6 rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-600">{{ error }}</p>
    <p v-else-if="!comunicaciones.length" class="mt-6 text-slate-500">No hay comunicados publicados.</p>

    <div v-else class="mt-5 grid items-start gap-3 md:grid-cols-2">
      <div v-for="c in comunicaciones" :key="c.id" class="grid gap-2">
        <ComunicadoCard :comunicado="c" completo />

        <template v-if="esAdmin">
          <div class="flex items-center justify-between gap-3 px-1 text-sm font-bold">
            <button type="button" @click="alternarVistas(c)" class="text-brand">
              Visto por {{ c.cant_vistas ?? 0 }} de {{ c.total_destinatarios ?? 0 }}
            </button>
            <button type="button" @click="eliminar(c)" class="text-red-600">Eliminar</button>
          </div>

          <div v-if="abierto === c.id" class="rounded-2xl border border-blue-100 bg-white p-3 text-sm shadow-sm">
            <p v-if="cargandoVistas" class="text-slate-500">Cargando...</p>
            <template v-else-if="vistas">
              <p class="font-bold text-slate-900">Lo vieron ({{ vistas.vieron.length }})</p>
              <p v-if="!vistas.vieron.length" class="text-slate-500">Todavía nadie.</p>
              <ul v-else class="mt-1 grid max-h-64 gap-1 overflow-y-auto">
                <li v-for="u in vistas.vieron" :key="u.id" class="flex items-center justify-between gap-2">
                  <span class="min-w-0 truncate text-slate-900">
                    {{ u.nombre }} <span class="text-xs text-slate-400">· {{ u.rol_display }}</span>
                  </span>
                  <span class="shrink-0 text-xs text-slate-400">{{ fechaHora(u.fecha) }}</span>
                </li>
              </ul>

              <p class="mt-3 font-bold text-slate-900">Todavía no lo vieron ({{ vistas.faltan.length }})</p>
              <p v-if="!vistas.faltan.length" class="text-slate-500">Lo vieron todos.</p>
              <ul v-else class="mt-1 grid max-h-64 gap-1 overflow-y-auto">
                <li v-for="u in vistas.faltan" :key="u.id" class="truncate text-slate-700">
                  {{ u.nombre }} <span class="text-xs text-slate-400">· {{ u.rol_display }}</span>
                </li>
              </ul>
            </template>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>