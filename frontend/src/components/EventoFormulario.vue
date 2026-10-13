<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import {
  crearEvento, editarEvento, getOpcionesEvento, previsualizarDestinatarios,
} from '@/services/calendario'
import { mensajeError } from '@/utils/errores'
import { TIPOS_EVENTO } from '@/utils/calendario'

const props = defineProps({
  evento: { type: Object, default: null }, // null = evento nuevo
  fechaInicial: { type: String, default: '' },
})
const emit = defineEmits(['guardado', 'cancelar'])

const esEdicion = computed(() => !!props.evento)

const form = ref({
  titulo: props.evento?.titulo ?? '',
  descripcion: props.evento?.descripcion ?? '',
  tipo: props.evento?.tipo ?? 'EVENTO',
  fecha_inicio: props.evento?.fecha_inicio ?? props.fechaInicial,
  fecha_fin: props.evento?.fecha_fin ?? props.fechaInicial,
  hora_inicio: props.evento?.hora_inicio?.slice(0, 5) ?? '',
  hora_fin: props.evento?.hora_fin?.slice(0, 5) ?? '',
})
const variosDias = ref(!!props.evento && props.evento.fecha_fin !== props.evento.fecha_inicio)

// Si dura un solo día, el fin acompaña al inicio
watch(
  () => form.value.fecha_inicio,
  (nueva) => {
    if (!variosDias.value || form.value.fecha_fin < nueva) form.value.fecha_fin = nueva
  },
)

// ---- Destinatarios ----
const opciones = ref(null)
const cargandoOpciones = ref(true)
const errorOpciones = ref('')

const todaEscuela = ref(false)
const categorias = ref([]) // ['DOCENTE', ...]
const cursosElegidos = ref([]) // ids
const rolesCurso = ref([]) // ['ALUMNO', 'FAMILIA', ...]

function restaurarDestinos(destinos) {
  todaEscuela.value = destinos.some((d) => d.tipo === 'TODOS')
  categorias.value = destinos.filter((d) => d.tipo === 'ROL').map((d) => d.rol)
  const deCurso = destinos.filter((d) => d.tipo === 'CURSO')
  cursosElegidos.value = [...new Set(deCurso.map((d) => d.curso))]
  rolesCurso.value = [...new Set(deCurso.map((d) => d.rol))]
}

onMounted(async () => {
  window.addEventListener('keydown', alTeclear)
  try {
    opciones.value = await getOpcionesEvento()
    if (props.evento) restaurarDestinos(props.evento.destinos)
    else rolesCurso.value = opciones.value.roles_curso.filter((r) => r.marcado).map((r) => r.valor)
  } catch (e) {
    errorOpciones.value = mensajeError(e, 'No pudimos cargar las opciones de destinatarios.')
  } finally {
    cargandoOpciones.value = false
  }
})

onUnmounted(() => window.removeEventListener('keydown', alTeclear))

function alTeclear(e) {
  if (e.key === 'Escape') emit('cancelar')
}

const destinos = computed(() => {
  if (todaEscuela.value) return [{ tipo: 'TODOS' }]
  const lista = categorias.value.map((rol) => ({ tipo: 'ROL', rol }))
  for (const curso of cursosElegidos.value) {
    for (const rol of rolesCurso.value) lista.push({ tipo: 'CURSO', rol, curso })
  }
  return lista
})

function alternarTodosLosCursos() {
  const todos = opciones.value.cursos.map((c) => c.id)
  cursosElegidos.value = cursosElegidos.value.length === todos.length ? [] : todos
}

// Recuento previo: a cuántas personas les va a llegar
const previa = ref(null)
let temporizador = null
let consulta = 0

watch(destinos, (lista) => {
  clearTimeout(temporizador)
  previa.value = null
  if (!lista.length) return
  const mia = ++consulta
  temporizador = setTimeout(async () => {
    try {
      const resultado = await previsualizarDestinatarios(lista)
      if (mia === consulta) previa.value = resultado
    } catch {
      if (mia === consulta) previa.value = null
    }
  }, 350)
})

// ---- Guardar ----
const guardando = ref(false)
const error = ref('')

async function guardar() {
  error.value = ''
  if (!destinos.value.length) {
    error.value = 'Elegí a quién le llega el evento.'
    return
  }
  guardando.value = true
  try {
    const f = form.value
    const datos = {
      titulo: f.titulo.trim(),
      descripcion: f.descripcion.trim(),
      tipo: f.tipo,
      fecha_inicio: f.fecha_inicio,
      fecha_fin: variosDias.value ? f.fecha_fin : f.fecha_inicio,
      hora_inicio: f.hora_inicio || null,
      hora_fin: f.hora_inicio && f.hora_fin ? f.hora_fin : null,
      destinos: destinos.value,
    }
    if (esEdicion.value) await editarEvento(props.evento.id, datos)
    else await crearEvento(datos)
    emit('guardado')
  } catch (e) {
    error.value = mensajeError(e, 'No se pudo guardar el evento.')
  } finally {
    guardando.value = false
  }
}
</script>

<template>
  <div
    class="fixed inset-0 z-40 flex items-end justify-center bg-black/40 md:items-center md:p-4"
    role="dialog"
    aria-modal="true"
    @click.self="emit('cancelar')"
  >
    <form
      @submit.prevent="guardar"
      class="grid max-h-[92dvh] w-full gap-4 overflow-y-auto rounded-t-3xl bg-white p-5 md:max-w-xl md:rounded-3xl"
    >
      <div class="flex items-start justify-between gap-3">
        <h2 class="text-xl font-extrabold text-slate-900">{{ esEdicion ? 'Editar evento' : 'Nuevo evento' }}</h2>
        <button type="button" @click="emit('cancelar')" aria-label="Cerrar" class="text-2xl leading-none text-slate-400">
          ×
        </button>
      </div>

      <label class="block">
        <span class="text-sm font-semibold text-slate-600">Título *</span>
        <input v-model="form.titulo" required maxlength="150" class="campo" />
      </label>

      <!-- Tipo -->
      <fieldset>
        <legend class="text-sm font-semibold text-slate-600">Tipo</legend>
        <div class="mt-1 flex flex-wrap gap-2">
          <button
            v-for="t in TIPOS_EVENTO"
            :key="t.valor"
            type="button"
            @click="form.tipo = t.valor"
            :aria-pressed="form.tipo === t.valor"
            class="rounded-sm px-3 py-1.5 text-[11px] font-bold uppercase tracking-wider text-slate-900 transition"
            :class="[t.fondo, form.tipo === t.valor ? 'ring-2 ring-slate-900 ring-offset-1' : 'opacity-60']"
          >
            {{ t.texto }}
          </button>
        </div>
      </fieldset>

      <!-- Fecha y hora -->
      <div class="grid gap-3 sm:grid-cols-2">
        <label class="block">
          <span class="text-sm font-semibold text-slate-600">Fecha *</span>
          <input v-model="form.fecha_inicio" required type="date" class="campo" />
        </label>
        <label class="flex items-end gap-2 pb-2 text-sm font-semibold text-slate-600">
          <input type="checkbox" v-model="variosDias" class="size-4" />
          Dura más de un día
        </label>
      </div>
      <label v-if="variosDias" class="block">
        <span class="text-sm font-semibold text-slate-600">Hasta el *</span>
        <input v-model="form.fecha_fin" required type="date" :min="form.fecha_inicio" class="campo" />
      </label>

      <div class="grid gap-3 sm:grid-cols-2">
        <label class="block">
          <span class="text-sm font-semibold text-slate-600">Hora de inicio (opcional)</span>
          <input v-model="form.hora_inicio" type="time" class="campo" />
        </label>
        <label class="block">
          <span class="text-sm font-semibold text-slate-600">Hora de fin (opcional)</span>
          <input v-model="form.hora_fin" type="time" :disabled="!form.hora_inicio" class="campo" />
        </label>
      </div>

      <label class="block">
        <span class="text-sm font-semibold text-slate-600">Descripción</span>
        <textarea v-model="form.descripcion" rows="3" class="campo"></textarea>
      </label>

      <!-- Destinatarios -->
      <fieldset class="grid gap-3 rounded-xl border border-slate-200 p-3">
        <legend class="px-1 text-sm font-bold text-slate-700">¿A quién le llega?</legend>

        <p v-if="cargandoOpciones" class="text-sm text-slate-500">Cargando...</p>
        <p v-else-if="errorOpciones" role="alert" class="text-sm font-semibold text-red-600">{{ errorOpciones }}</p>

        <template v-else-if="opciones">
          <label v-if="opciones.toda_escuela" class="flex items-center gap-2 text-sm font-bold text-brand">
            <input type="checkbox" v-model="todaEscuela" class="size-4" />
            Toda la escuela
          </label>

          <template v-if="!todaEscuela">
            <!-- Categorías completas (conducción) -->
            <div v-if="opciones.categorias.length">
              <p class="text-xs font-bold uppercase tracking-wide text-slate-400">Categorías completas</p>
              <div class="mt-1 flex flex-wrap gap-x-4 gap-y-1">
                <label v-for="c in opciones.categorias" :key="c.valor" class="flex items-center gap-2 text-sm text-slate-800">
                  <input type="checkbox" :value="c.valor" v-model="categorias" class="size-4" />
                  {{ c.texto }}
                </label>
              </div>
            </div>

            <!-- Cursos -->
            <div>
              <div class="flex items-center justify-between gap-2">
                <p class="text-xs font-bold uppercase tracking-wide text-slate-400">Por curso</p>
                <button
                  v-if="opciones.cursos.length > 1"
                  type="button"
                  @click="alternarTodosLosCursos"
                  class="text-xs font-bold text-brand"
                >
                  {{ cursosElegidos.length === opciones.cursos.length ? 'Quitar todos' : 'Elegir todos' }}
                </button>
              </div>
              <p v-if="!opciones.cursos.length" class="mt-1 text-sm text-slate-500">
                No tenés cursos asignados, así que por ahora no podés dirigir eventos a un curso.
              </p>
              <template v-else>
                <div class="mt-1 grid max-h-36 gap-1 overflow-y-auto sm:grid-cols-2">
                  <label v-for="c in opciones.cursos" :key="c.id" class="flex items-center gap-2 text-sm text-slate-800">
                    <input type="checkbox" :value="c.id" v-model="cursosElegidos" class="size-4" />
                    {{ c.nombre }}
                    <span class="text-xs text-slate-400">{{ c.anio_lectivo }}</span>
                  </label>
                </div>
                <p class="mt-2 text-xs font-bold uppercase tracking-wide text-slate-400">De esos cursos, a quiénes</p>
                <div class="mt-1 flex flex-wrap gap-x-4 gap-y-1">
                  <label v-for="r in opciones.roles_curso" :key="r.valor" class="flex items-center gap-2 text-sm text-slate-800">
                    <input type="checkbox" :value="r.valor" v-model="rolesCurso" class="size-4" />
                    {{ r.texto }}
                  </label>
                </div>
              </template>
            </div>
          </template>

          <!-- Recuento previo -->
          <div v-if="previa" class="rounded-xl bg-blue-50 p-3">
            <p class="text-sm font-bold text-brand">
              Lo van a ver {{ previa.total }} {{ previa.total === 1 ? 'persona' : 'personas' }}
            </p>
            <ul class="mt-1 grid gap-0.5 text-xs text-slate-600">
              <li v-for="d in previa.detalle" :key="d.texto">{{ d.texto }}: {{ d.cantidad }}</li>
            </ul>
          </div>
          <p v-else-if="!destinos.length" class="text-xs text-amber-600">Elegí al menos un destinatario.</p>
        </template>
      </fieldset>

      <p v-if="error" role="alert" class="rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-600">{{ error }}</p>

      <div class="flex gap-3">
        <button type="submit" :disabled="guardando || cargandoOpciones" class="boton-principal">
          {{ guardando ? 'Guardando...' : esEdicion ? 'Guardar cambios' : 'Publicar' }}
        </button>
        <button type="button" @click="emit('cancelar')" class="rounded-xl px-4 font-bold text-slate-500 hover:bg-slate-100">
          Cancelar
        </button>
      </div>
    </form>
  </div>
</template>