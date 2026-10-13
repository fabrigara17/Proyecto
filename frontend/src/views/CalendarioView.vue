<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { eliminarEvento, getEventos } from '@/services/calendario'
import { mensajeError } from '@/utils/errores'
import { fechaCorta, fechaLarga } from '@/utils/formato'
import {
  aISO, DIAS, eventosPorDia, horaCorta, nombreMes, semanasDelMes, TIPO_POR_VALOR, TIPOS_EVENTO,
} from '@/utils/calendario'
import AppIcon from '@/components/AppIcon.vue'
import EventoFormulario from '@/components/EventoFormulario.vue'

const auth = useAuthStore()
const puedeCrear = computed(() => ['ADMIN', 'CONDUCCION', 'DOCENTE', 'PRECEPTOR'].includes(auth.rol))

const hoy = new Date()
const anio = ref(hoy.getFullYear())
const mes0 = ref(hoy.getMonth())

const eventos = ref([])
const cargando = ref(true)
const error = ref('')

const diaAbierto = ref(null) // 'YYYY-MM-DD' del día cuya lista está abierta
const formularioAbierto = ref(false)
const eventoEnEdicion = ref(null)
const fechaNueva = ref('')

const semanas = computed(() => semanasDelMes(anio.value, mes0.value))
const rango = computed(() => ({
  desde: semanas.value[0][0].iso,
  hasta: semanas.value.at(-1).at(-1).iso,
}))
const porDia = computed(() => eventosPorDia(eventos.value, rango.value.desde, rango.value.hasta))
const listaDelDia = computed(() => (diaAbierto.value ? porDia.value[diaAbierto.value] ?? [] : []))

// Si cambia de mes rápido, descartamos las respuestas viejas
let carga = 0

async function cargar() {
  const mia = ++carga
  cargando.value = true
  error.value = ''
  try {
    const lista = await getEventos(rango.value.desde, rango.value.hasta)
    if (mia === carga) eventos.value = lista
  } catch (e) {
    if (mia === carga) error.value = mensajeError(e, 'No pudimos cargar el calendario. Probá de nuevo.')
  } finally {
    if (mia === carga) cargando.value = false
  }
}

watch([anio, mes0], cargar, { immediate: true })

function mover(delta) {
  const d = new Date(anio.value, mes0.value + delta, 1)
  anio.value = d.getFullYear()
  mes0.value = d.getMonth()
}

function irAHoy() {
  const d = new Date()
  anio.value = d.getFullYear()
  mes0.value = d.getMonth()
}

// ---- Lista del día ----
function abrirDia(iso) {
  diaAbierto.value = iso
}

function cerrarDia() {
  diaAbierto.value = null
}

function alTeclear(e) {
  if (e.key === 'Escape' && !formularioAbierto.value) cerrarDia()
}

onMounted(() => window.addEventListener('keydown', alTeclear))
onUnmounted(() => window.removeEventListener('keydown', alTeclear))

function cuando(e) {
  const hora = e.hora_inicio
    ? `${horaCorta(e.hora_inicio)}${e.hora_fin ? ` a ${horaCorta(e.hora_fin)}` : ''} hs`
    : 'Todo el día'
  return e.fecha_fin !== e.fecha_inicio
    ? `${fechaCorta(e.fecha_inicio)} al ${fechaCorta(e.fecha_fin)} · ${hora}`
    : hora
}

// ---- Alta, edición y baja ----
function nuevoEvento(fecha) {
  eventoEnEdicion.value = null
  fechaNueva.value = fecha
  formularioAbierto.value = true
}

function editar(e) {
  eventoEnEdicion.value = e
  fechaNueva.value = e.fecha_inicio
  formularioAbierto.value = true
}

function cerrarFormulario() {
  formularioAbierto.value = false
  eventoEnEdicion.value = null
}

async function alGuardar() {
  cerrarFormulario()
  await cargar()
}

async function eliminar(e) {
  if (!window.confirm(`¿Eliminar el evento "${e.titulo}"?`)) return
  error.value = ''
  try {
    await eliminarEvento(e.id)
    await cargar()
  } catch (err) {
    error.value = mensajeError(err, 'No se pudo eliminar el evento.')
  }
}
</script>

<template>
  <div class="pagina">
    <!-- Mes y navegación -->
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-2">
        <button
          type="button"
          @click="mover(-1)"
          aria-label="Mes anterior"
          class="grid size-10 place-items-center rounded-xl bg-white text-brand shadow-sm ring-1 ring-slate-100 hover:bg-blue-50"
        >
          <AppIcon name="arrow-right" class="size-5 rotate-180" />
        </button>
        <button
          type="button"
          @click="mover(1)"
          aria-label="Mes siguiente"
          class="grid size-10 place-items-center rounded-xl bg-white text-brand shadow-sm ring-1 ring-slate-100 hover:bg-blue-50"
        >
          <AppIcon name="arrow-right" class="size-5" />
        </button>
        <button type="button" @click="irAHoy" class="rounded-xl px-3 py-2 text-sm font-bold text-brand hover:bg-blue-50">
          Hoy
        </button>
      </div>
      <button v-if="puedeCrear" type="button" @click="nuevoEvento(aISO(new Date()))" class="boton-principal !w-auto px-4">
        Nuevo evento
      </button>
    </div>

    <h1 class="mt-4 text-3xl font-extrabold uppercase leading-none tracking-tight text-slate-900 md:text-5xl">
      {{ nombreMes(anio, mes0) }}
    </h1>

    <!-- Leyenda de colores -->
    <div class="mt-3 flex flex-wrap gap-2">
      <span
        v-for="t in TIPOS_EVENTO"
        :key="t.valor"
        class="rounded-sm px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-slate-900"
        :class="t.fondo"
      >
        {{ t.texto }}
      </span>
    </div>

    <p v-if="error" role="alert" class="mt-3 rounded-xl bg-red-50 p-3 text-sm font-semibold text-red-600">{{ error }}</p>

    <!-- Grilla mensual -->
    <div
      class="mt-4 overflow-hidden rounded-xl border border-slate-300 bg-stone-100 transition"
      :class="{ 'opacity-60': cargando }"
    >
      <div
        class="grid grid-cols-[1.75rem_repeat(7,minmax(0,1fr))] border-b border-slate-300 bg-white text-center text-[10px] font-semibold uppercase tracking-wide text-slate-600 md:text-xs"
      >
        <div></div>
        <div v-for="(d, i) in DIAS" :key="i" class="py-2">
          <span class="md:hidden">{{ d.corto }}</span>
          <span class="hidden md:inline">{{ d.largo }}</span>
        </div>
      </div>

      <div
        v-for="(semana, i) in semanas"
        :key="semana[0].iso"
        class="grid grid-cols-[1.75rem_repeat(7,minmax(0,1fr))] border-b border-slate-300 last:border-b-0"
      >
        <div class="grid place-items-center bg-black text-white">
          <span class="rotate-180 text-[9px] font-bold uppercase tracking-widest [writing-mode:vertical-rl] md:text-[10px]">
            Semana {{ i + 1 }}
          </span>
        </div>

        <button
          v-for="dia in semana"
          :key="dia.iso"
          type="button"
          @click="abrirDia(dia.iso)"
          class="flex min-h-16 flex-col items-start border-l border-slate-300 p-1 text-left transition hover:bg-white/70 md:min-h-28 md:p-1.5"
          :class="dia.delMes ? 'bg-stone-100' : 'bg-stone-200/50'"
          :aria-label="`${dia.numero}, ${(porDia[dia.iso] ?? []).length} eventos`"
        >
          <span
            class="grid size-5 place-items-center rounded-full text-[11px] font-bold md:size-6 md:text-xs"
            :class="dia.esHoy ? 'bg-brand text-white' : dia.delMes ? 'text-slate-700' : 'text-slate-400'"
          >
            {{ dia.numero }}
          </span>

          <!-- Escritorio: tarjetas de color -->
          <span class="mt-1 hidden w-full gap-1 md:grid">
            <span
              v-for="e in (porDia[dia.iso] ?? []).slice(0, 3)"
              :key="e.id"
              class="block truncate rounded px-1.5 py-1 text-[11px] font-semibold leading-tight text-slate-900"
              :class="TIPO_POR_VALOR[e.tipo].fondo"
            >
              <span v-if="e.hora_inicio" class="font-bold">{{ horaCorta(e.hora_inicio) }}</span>
              {{ e.titulo }}
            </span>
            <span v-if="(porDia[dia.iso] ?? []).length > 3" class="px-1 text-[11px] font-bold text-slate-500">
              +{{ porDia[dia.iso].length - 3 }} más
            </span>
          </span>

          <!-- Celular: puntos de color -->
          <span class="mt-1 flex flex-wrap gap-0.5 md:hidden">
            <span
              v-for="e in (porDia[dia.iso] ?? []).slice(0, 4)"
              :key="e.id"
              class="size-2 rounded-full"
              :class="TIPO_POR_VALOR[e.tipo].fondo"
            ></span>
          </span>
        </button>
      </div>
    </div>

    <!-- Lista de eventos del día -->
    <div
      v-if="diaAbierto"
      class="fixed inset-0 z-30 flex items-end justify-center bg-black/40 md:items-center md:p-4"
      role="dialog"
      aria-modal="true"
      @click.self="cerrarDia"
    >
      <div class="max-h-[85dvh] w-full overflow-y-auto rounded-t-3xl bg-white p-5 md:max-w-lg md:rounded-3xl">
        <div class="flex items-start justify-between gap-3">
          <h2 class="text-xl font-extrabold text-slate-900 first-letter:uppercase">{{ fechaLarga(diaAbierto) }}</h2>
          <button type="button" @click="cerrarDia" aria-label="Cerrar" class="text-2xl leading-none text-slate-400">×</button>
        </div>

        <p v-if="!listaDelDia.length" class="mt-4 text-slate-500">No hay eventos este día.</p>
        <ul v-else class="mt-4 grid gap-3">
          <li v-for="e in listaDelDia" :key="e.id" class="overflow-hidden rounded-2xl border border-slate-200">
            <div class="h-1.5" :class="TIPO_POR_VALOR[e.tipo].fondo"></div>
            <div class="p-3">
              <div class="flex items-start justify-between gap-2">
                <span
                  class="rounded-full px-2 py-0.5 text-[11px] font-bold uppercase"
                  :class="TIPO_POR_VALOR[e.tipo].suave"
                >
                  {{ e.tipo_display }}
                </span>
                <span class="text-right text-xs font-semibold text-slate-500">{{ cuando(e) }}</span>
              </div>
              <p class="mt-1 font-bold text-slate-900">{{ e.titulo }}</p>
              <p v-if="e.descripcion" class="mt-1 whitespace-pre-line text-sm text-slate-700">{{ e.descripcion }}</p>
              <p class="mt-2 text-xs text-slate-500">
                Publicó: {{ e.creado_por_nombre ?? 'un usuario eliminado' }}
                <template v-if="e.creado_por_rol">· {{ e.creado_por_rol }}</template>
              </p>
              <p class="text-xs text-slate-500">Para: {{ e.destinos.map((d) => d.texto).join(' · ') }}</p>
              <div v-if="e.puede_editar" class="mt-2 flex gap-4 text-sm font-bold">
                <button type="button" @click="editar(e)" class="text-brand">Editar</button>
                <button type="button" @click="eliminar(e)" class="text-red-600">Eliminar</button>
              </div>
            </div>
          </li>
        </ul>

        <button v-if="puedeCrear" type="button" @click="nuevoEvento(diaAbierto)" class="boton-principal mt-4">
          Agregar evento este día
        </button>
      </div>
    </div>

    <EventoFormulario
      v-if="formularioAbierto"
      :evento="eventoEnEdicion"
      :fecha-inicial="fechaNueva"
      @cancelar="cerrarFormulario"
      @guardado="alGuardar"
    />
  </div>
</template>