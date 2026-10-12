<script setup>
import { nextTick, onMounted, ref } from 'vue'
import { enviarConsulta, getConsultas } from '@/services/materiales'
import { fechaHora } from '@/utils/formato'

const props = defineProps({ materialId: { type: Number, required: true } })
const emit = defineEmits(['enviada'])

const ROLES = {
  DOCENTE: 'Docente',
  FAMILIA: 'Familia',
  ALUMNO: 'Alumno',
  PRECEPTOR: 'Preceptor',
  ADMIN: 'Institución',
}

const mensajes = ref([])
const cargando = ref(true)
const error = ref('')
const texto = ref('')
const enviando = ref(false)
const lista = ref(null)

async function irAlFinal() {
  await nextTick()
  if (lista.value) lista.value.scrollTop = lista.value.scrollHeight
}

onMounted(async () => {
  try {
    mensajes.value = await getConsultas(props.materialId)
  } catch {
    error.value = 'No pudimos cargar las consultas. Probá de nuevo en un momento.'
  } finally {
    cargando.value = false
    irAlFinal()
  }
})

async function enviar() {
  const t = texto.value.trim()
  if (!t || enviando.value) return
  enviando.value = true
  error.value = ''
  try {
    const nuevo = await enviarConsulta(props.materialId, t)
    mensajes.value.push(nuevo)
    texto.value = ''
    emit('enviada')
    irAlFinal()
  } catch (e) {
    const data = e.response?.data
    error.value = data && typeof data === 'object'
      ? Object.values(data).flat().join(' ')
      : 'No se pudo enviar. Probá de nuevo.'
  } finally {
    enviando.value = false
  }
}
</script>

<template>
  <div class="mt-3 rounded-2xl bg-slate-50 p-3 ring-1 ring-slate-100">
    <div ref="lista" class="max-h-72 space-y-2 overflow-y-auto pr-1">
      <p v-if="cargando" class="text-sm text-slate-500">Cargando consultas...</p>
      <p v-else-if="!mensajes.length" class="text-sm text-slate-500">
        Todavía no hay consultas. ¡Escribí la primera!
      </p>

      <div
        v-for="m in mensajes"
        :key="m.id"
        class="flex"
        :class="m.es_mio ? 'justify-end' : 'justify-start'"
      >
        <div
          class="max-w-[85%] rounded-2xl px-3 py-2 text-sm"
          :class="m.autor_rol === 'DOCENTE'
            ? 'bg-brand text-white'
            : m.es_mio
              ? 'bg-blue-100 text-slate-800'
              : 'bg-white text-slate-800 ring-1 ring-slate-200'"
        >
          <p class="text-[11px] font-bold" :class="m.autor_rol === 'DOCENTE' ? 'text-white/80' : 'text-brand'">
            {{ m.es_mio ? 'Vos' : m.autor_nombre }} · {{ ROLES[m.autor_rol] ?? '' }}
          </p>
          <p class="break-words whitespace-pre-line">{{ m.texto }}</p>
          <p class="mt-0.5 text-[10px] opacity-70">{{ fechaHora(m.fecha) }}</p>
        </div>
      </div>
    </div>

    <p v-if="error" role="alert" class="mt-2 rounded-lg bg-red-50 px-3 py-2 text-xs font-semibold text-red-600">
      {{ error }}
    </p>

    <form @submit.prevent="enviar" class="mt-3 flex items-center gap-2">
      <input
        v-model="texto"
        maxlength="500"
        placeholder="Escribí tu consulta..."
        class="campo flex-1"
      />
      <button
        type="submit"
        :disabled="enviando || !texto.trim()"
        class="rounded-xl bg-brand px-4 py-3 text-sm font-bold text-white disabled:opacity-50"
      >
        Enviar
      </button>
    </form>
  </div>
</template>