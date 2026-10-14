<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import chatService from '@/services/chat'
import AppIcon from '@/components/AppIcon.vue'
import { useAuthStore } from '@/stores/auth'
import { mensajeError } from '@/utils/errores'

// Mismos límites que valida el backend (chat/serializers.py)
const EXTENSIONES_PERMITIDAS = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.jpg', '.jpeg', '.png', '.txt']
const MAX_MB = 10

const auth = useAuthStore()
const conversaciones = ref([])
const conversacionActiva = ref(null)
const mensajes = ref([])
const nuevoTexto = ref('')
const cargando = ref(false)

const archivoSeleccionado = ref(null)
const inputArchivo = ref(null)
const enviando = ref(false)
const errorEnvio = ref('')

const modalAbierto = ref(false)
const usuariosDisponibles = ref([])
const filtroRol = ref('todos')
const busquedaTexto = ref('')

const esAlumnoOFamiliar = computed(() => {
  const r = String(auth.rol || '').toUpperCase()
  return r === 'ALUMNO' || r === 'FAMILIA'
})

async function cargarConversaciones() {
  try {
    conversaciones.value = await chatService.obtenerConversaciones()
  } catch (error) {
    console.error("Error al cargar conversaciones:", error)
  }
}

function nombreOtro(conv) {
  if (!conv) return ''
  const otro = conv.participante_1 === auth.usuario?.id
    ? conv.participante_2_detalles
    : conv.participante_1_detalles
  if (!otro) return 'Usuario'
  const nombre = `${otro.first_name || ''} ${otro.last_name || ''}`.trim()
  return nombre || otro.username
}

function previewUltimo(conv) {
  const m = conv.ultimo_mensaje
  if (!m) return 'Sin mensajes aún'
  return m.texto || `📎 ${m.archivo_nombre}`
}

async function seleccionarChat(conv) {
  conversacionActiva.value = conv
  limpiarArchivo()
  errorEnvio.value = ''
  cargando.value = true
  try {
    mensajes.value = await chatService.obtenerMensajes(conv.id)
  } catch (error) {
    console.error("Error al cargar mensajes:", error)
  } finally {
    cargando.value = false
  }
}

function elegirArchivo(e) {
  const f = e.target.files?.[0]
  e.target.value = '' // permite volver a elegir el mismo archivo
  if (!f) return
  errorEnvio.value = ''

  const ext = f.name.includes('.') ? '.' + f.name.split('.').pop().toLowerCase() : ''
  if (!EXTENSIONES_PERMITIDAS.includes(ext)) {
    errorEnvio.value = `Tipo de archivo no permitido. Podés enviar: ${EXTENSIONES_PERMITIDAS.map(x => x.slice(1)).join(', ')}.`
    return
  }
  if (f.size > MAX_MB * 1024 * 1024) {
    errorEnvio.value = `El archivo supera los ${MAX_MB} MB.`
    return
  }
  archivoSeleccionado.value = f
}

function limpiarArchivo() {
  archivoSeleccionado.value = null
  if (inputArchivo.value) inputArchivo.value.value = ''
}

function tamanioLegible(bytes) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

async function descargarAdjunto(msg) {
  try {
    await chatService.descargarAdjunto(msg)
  } catch (error) {
    console.error("Error al descargar archivo:", error)
    errorEnvio.value = 'No se pudo descargar el archivo.'
  }
}

async function abrirModalNuevaConversacion() {
  busquedaTexto.value = ''
  modalAbierto.value = true
  await cargarUsuariosDisponibles()
}

async function cargarUsuariosDisponibles() {
  try {
    const response = await chatService.obtenerUsuariosDisponibles(filtroRol.value)
    usuariosDisponibles.value = response.data
  } catch (error) {
    console.error("Error al cargar usuarios disponibles:", error)
    usuariosDisponibles.value = []
  }
}

watch(filtroRol, () => {
  cargarUsuariosDisponibles()
})

const usuariosFiltrados = computed(() => {
  let lista = usuariosDisponibles.value
  if (busquedaTexto.value.trim()) {
    const txt = busquedaTexto.value.toLowerCase()
    lista = lista.filter(u => {
      const nom = `${u.first_name || ''} ${u.last_name || ''} ${u.username || ''}`.toLowerCase()
      return nom.includes(txt)
    })
  }
  return lista
})

async function iniciarChatCon(usuarioId) {
  // Si ya existe una conversación con esa persona, la abrimos en vez de duplicarla
  const existente = conversaciones.value.find(
    c => c.participante_1 === usuarioId || c.participante_2 === usuarioId
  )
  if (existente) {
    modalAbierto.value = false
    seleccionarChat(existente)
    return
  }

  try {
    const response = await chatService.crearConversacion({ participante_2: usuarioId })
    modalAbierto.value = false
    await cargarConversaciones()
    seleccionarChat(response.data)
  } catch (error) {
    console.error("Error al iniciar conversación:", error)
  }
}

async function enviarMensaje() {
  const texto = nuevoTexto.value.trim()
  const archivo = archivoSeleccionado.value
  if ((!texto && !archivo) || !conversacionActiva.value || enviando.value) return

  enviando.value = true
  errorEnvio.value = ''
  try {
    const response = await chatService.enviarMensaje({
      conversacion: conversacionActiva.value.id,
      texto,
      archivo,
    })
    mensajes.value.push(response.data)
    nuevoTexto.value = ''
    limpiarArchivo()
    cargarConversaciones() // refresca el último mensaje en la lista
  } catch (error) {
    console.error("Error al enviar mensaje:", error)
    errorEnvio.value = mensajeError(error, 'No se pudo enviar el mensaje.')
  } finally {
    enviando.value = false
  }
}

onMounted(() => {
  cargarConversaciones()
})
</script>

<template>
  <div class="flex h-[calc(100dvh-env(safe-area-inset-bottom))] md:h-screen bg-slate-50 overflow-hidden">
    <!-- Panel Izquierdo -->
    <aside class="w-full md:w-80 bg-white border-r border-slate-200 flex flex-col" :class="{ 'hidden md:flex': conversacionActiva }">
      <div class="p-4 border-b border-slate-200 flex justify-between items-center">
        <h1 class="text-xl font-bold text-slate-800">Mensajes</h1>
        <button 
          v-if="!esAlumnoOFamiliar"
          @click="abrirModalNuevaConversacion" 
          class="bg-brand text-white px-3 py-1.5 rounded-xl text-xs font-semibold hover:bg-brand-dark transition flex items-center gap-1.5"
        >
          <AppIcon name="user-plus" class="size-4" />
          Nuevo Chat
        </button>
      </div>
      
      <div class="flex-1 overflow-y-auto divide-y divide-slate-100">
        <div v-if="conversaciones.length === 0" class="p-6 text-center text-slate-400 text-sm">
          No tienes conversaciones activas.
        </div>
        
        <div 
          v-for="conv in conversaciones" 
          :key="conv.id"
          @click="seleccionarChat(conv)"
          class="p-4 hover:bg-slate-50 cursor-pointer transition flex items-center gap-3"
          :class="{ 'bg-blue-50/60': conversacionActiva?.id === conv.id }"
        >
          <div class="size-10 rounded-full bg-blue-100 text-blue-600 font-bold flex items-center justify-center shrink-0">
            <AppIcon name="user" class="size-5" />
          </div>
          <div class="flex-1 min-w-0">
            <h2 class="font-semibold text-slate-800 truncate">
              {{ nombreOtro(conv) }}
            </h2>
            <p class="text-xs text-slate-500 truncate">
              {{ previewUltimo(conv) }}
            </p>
          </div>
        </div>
      </div>
    </aside>

    <!-- Panel Derecho -->
    <main class="flex-1 flex flex-col bg-white md:bg-slate-50" :class="{ 'hidden md:flex': !conversacionActiva }">
      <template v-if="conversacionActiva">
        <div class="p-4 bg-white border-b border-slate-200 flex items-center gap-3 shadow-xs">
          <button @click="conversacionActiva = null" class="md:hidden text-slate-500">
            <AppIcon name="arrow-left" class="size-6" />
          </button>
          <h2 class="font-bold text-slate-800 truncate flex-1 min-w-0">{{ nombreOtro(conversacionActiva) }}</h2>
        </div>

        <div class="flex-1 overflow-y-auto p-4 space-y-3 flex flex-col">
          <div v-if="cargando" class="text-center text-slate-400 py-4">Cargando mensajes...</div>
          <div 
            v-for="msg in mensajes" 
            :key="msg.id"
            class="max-w-[75%] rounded-2xl px-4 py-2 text-sm shadow-xs"
            :class="msg.remisor === auth.usuario?.id ? 'bg-brand text-white self-end rounded-br-none' : 'bg-white text-slate-800 self-start border border-slate-200 rounded-bl-none'"
          >
            <button
              v-if="msg.archivo_nombre"
              type="button"
              @click="descargarAdjunto(msg)"
              class="flex items-center gap-2 rounded-lg px-2 py-1.5 mb-1 w-full text-left transition"
              :class="msg.remisor === auth.usuario?.id ? 'bg-white/15 hover:bg-white/25' : 'bg-slate-100 hover:bg-slate-200'"
            >
              <AppIcon name="document" class="size-5 shrink-0" />
              <span class="truncate flex-1 min-w-0 underline">{{ msg.archivo_nombre }}</span>
              <AppIcon name="download" class="size-4 shrink-0" />
            </button>
            <p v-if="msg.texto" class="whitespace-pre-wrap break-words">{{ msg.texto }}</p>
            <span class="text-[10px] opacity-75 block text-right mt-1">
              {{ new Date(msg.fecha_envio).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }}
            </span>
          </div>
        </div>

        <div class="bg-white border-t border-slate-200">
          <p v-if="errorEnvio" class="px-4 pt-2 text-xs text-red-600">{{ errorEnvio }}</p>

          <!-- Archivo elegido, pendiente de enviar -->
          <div v-if="archivoSeleccionado" class="mx-3 mt-3 flex items-center gap-2 rounded-xl bg-slate-100 px-3 py-2 text-sm text-slate-700">
            <AppIcon name="document" class="size-5 shrink-0" />
            <span class="truncate flex-1 min-w-0">{{ archivoSeleccionado.name }}</span>
            <span class="text-xs text-slate-500 shrink-0">{{ tamanioLegible(archivoSeleccionado.size) }}</span>
            <button type="button" @click="limpiarArchivo" class="text-slate-400 hover:text-slate-600 shrink-0" aria-label="Quitar archivo">
              <AppIcon name="x-mark" class="size-4" />
            </button>
          </div>

          <form @submit.prevent="enviarMensaje" class="p-3 flex gap-2">
            <input
              ref="inputArchivo"
              type="file"
              class="hidden"
              :accept="EXTENSIONES_PERMITIDAS.join(',')"
              @change="elegirArchivo"
            />
            <button
              type="button"
              @click="inputArchivo.click()"
              class="border border-slate-300 text-slate-500 px-3 py-2 rounded-xl hover:bg-slate-50 transition flex items-center justify-center"
              aria-label="Adjuntar archivo"
            >
              <AppIcon name="paper-clip" class="size-5" />
            </button>
            <input 
              type="text" 
              v-model="nuevoTexto" 
              placeholder="Escribe un mensaje..." 
              class="flex-1 min-w-0 border border-slate-300 rounded-xl px-4 py-2 text-sm focus:outline-none focus:border-brand"
            />
            <button
              type="submit"
              :disabled="enviando"
              class="bg-brand text-white px-4 py-2 rounded-xl font-semibold flex items-center justify-center hover:bg-brand-dark transition disabled:opacity-60"
            >
              <AppIcon name="paper-airplane" class="size-5" />
            </button>
          </form>
        </div>
      </template>

      <div v-else class="flex-1 hidden md:flex flex-col items-center justify-center text-slate-400 p-6">
        <AppIcon name="chat" class="size-16 mb-2 opacity-40" />
        <p class="text-base font-medium">Selecciona una conversación</p>
      </div>
    </main>

    <!-- MODAL DE NUEVA CONVERSACIÓN -->
    <div v-if="modalAbierto" class="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
      <div class="bg-white rounded-2xl w-full max-w-md max-h-[80vh] flex flex-col shadow-xl overflow-hidden">
        <div class="p-4 border-b border-slate-200 flex justify-between items-center">
          <h3 class="font-bold text-slate-800 text-lg">Iniciar Nueva Conversación</h3>
          <button @click="modalAbierto = false" class="text-slate-400 hover:text-slate-600">✕</button>
        </div>

        <div class="p-4 border-b border-slate-100 space-y-3">
          <input 
            type="text" 
            v-model="busquedaTexto" 
            placeholder="Buscar por nombre..." 
            class="w-full border border-slate-300 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-brand"
          />
          <div class="flex gap-1 overflow-x-auto pb-1 text-xs font-semibold">
            <button @click="filtroRol = 'todos'" :class="filtroRol === 'todos' ? 'bg-brand text-white' : 'bg-slate-100 text-slate-600'" class="px-3 py-1.5 rounded-lg transition whitespace-nowrap">Todos</button>
            <button @click="filtroRol = 'conduccion'" :class="filtroRol === 'conduccion' ? 'bg-brand text-white' : 'bg-slate-100 text-slate-600'" class="px-3 py-1.5 rounded-lg transition whitespace-nowrap">Conducción</button>
            <button @click="filtroRol = 'preceptor'" :class="filtroRol === 'preceptor' ? 'bg-brand text-white' : 'bg-slate-100 text-slate-600'" class="px-3 py-1.5 rounded-lg transition whitespace-nowrap">Preceptores</button>
            <button @click="filtroRol = 'docente'" :class="filtroRol === 'docente' ? 'bg-brand text-white' : 'bg-slate-100 text-slate-600'" class="px-3 py-1.5 rounded-lg transition whitespace-nowrap">Docentes</button>
            <button @click="filtroRol = 'alumno'" :class="filtroRol === 'alumno' ? 'bg-brand text-white' : 'bg-slate-100 text-slate-600'" class="px-3 py-1.5 rounded-lg transition whitespace-nowrap">Alumnos/Familias</button>
          </div>
        </div>

        <div class="flex-1 overflow-y-auto divide-y divide-slate-100 p-2">
          <div v-if="usuariosFiltrados.length === 0" class="text-center py-6 text-slate-400 text-sm">
            No se encontraron usuarios.
          </div>
          <div 
            v-for="u in usuariosFiltrados" 
            :key="u.id"
            @click="iniciarChatCon(u.id)"
            class="p-3 hover:bg-slate-50 rounded-xl cursor-pointer transition flex items-center justify-between"
          >
            <div>
              <p class="font-semibold text-slate-800 text-sm">{{ (u.first_name || u.last_name) ? `${u.first_name || ''} ${u.last_name || ''}` : u.username }}</p>
              <span class="text-xs uppercase bg-slate-100 text-slate-600 px-2 py-0.5 rounded-md font-bold">{{ u.rol || 'Usuario' }}</span>
            </div>
            <AppIcon name="chat" class="size-5 text-brand" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>