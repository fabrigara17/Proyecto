<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import chatService from '@/services/chat'
import api from '@/services/api'
import AppIcon from '@/components/AppIcon.vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const conversaciones = ref([])
const conversacionActiva = ref(null)
const mensajes = ref([])
const nuevoTexto = ref('')
const cargando = ref(false)

const modalAbierto = ref(false)
const usuariosDisponibles = ref([])
const filtroRol = ref('todos')
const busquedaTexto = ref('')

const esAlumnoOFamiliar = computed(() => {
  const r = String(auth.rol || '').toUpperCase()
  return r === 'ALUMNO' || r === 'FAMILIAR'
})

async function cargarConversaciones() {
  try {
    const response = await chatService.obtenerConversaciones()
    conversaciones.value = response.data
  } catch (error) {
    console.error("Error al cargar conversaciones:", error)
  }
}

async function seleccionarChat(conv) {
  conversacionActiva.value = conv
  cargando.value = true
  try {
    const response = await chatService.obtenerMensajes(conv.id)
    mensajes.value = response.data
  } catch (error) {
    console.error("Error al cargar mensajes:", error)
  } finally {
    cargando.value = false
  }
}

async function abrirModalNuevaConversacion() {
  modalAbierto.value = true
  await cargarUsuariosDisponibles()
}

async function cargarUsuariosDisponibles() {
  try {
    const response = await api.get(`/conversaciones/usuarios_disponibles/?rol=${filtroRol.value}`)
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
  if (!nuevoTexto.value.trim() || !conversacionActiva.value) return
  const textoTemp = nuevoTexto.value
  nuevoTexto.value = ''

  try {
    const response = await chatService.enviarMensaje({
      conversacion: conversacionActiva.value.id,
      texto: textoTemp
    })
    mensajes.value.push(response.data)
  } catch (error) {
    console.error("Error al enviar mensaje:", error)
    nuevoTexto.value = textoTemp
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
              {{ conv.participante_1.id === auth.user?.id ? (conv.participante_2.first_name || conv.participante_2.username) : (conv.participante_1.first_name || conv.participante_1.username) }}
            </h2>
            <p class="text-xs text-slate-500 truncate">
              {{ conv.ultimo_mensaje ? conv.ultimo_mensaje.texto : 'Sin mensajes aún' }}
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
          <h2 class="font-bold text-slate-800">Conversación</h2>
        </div>

        <div class="flex-1 overflow-y-auto p-4 space-y-3 flex flex-col">
          <div v-if="cargando" class="text-center text-slate-400 py-4">Cargando mensajes...</div>
          <div 
            v-for="msg in mensajes" 
            :key="msg.id"
            class="max-w-[75%] rounded-2xl px-4 py-2 text-sm shadow-xs"
            :class="msg.remisor === auth.user?.id ? 'bg-brand text-white self-end rounded-br-none' : 'bg-white text-slate-800 self-start border border-slate-200 rounded-bl-none'"
          >
            <p>{{ msg.texto }}</p>
            <span class="text-[10px] opacity-75 block text-right mt-1">
              {{ new Date(msg.fecha_envio).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }}
            </span>
          </div>
        </div>

        <form @submit.prevent="enviarMensaje" class="p-3 bg-white border-t border-slate-200 flex gap-2">
          <input 
            type="text" 
            v-model="nuevoTexto" 
            placeholder="Escribe un mensaje..." 
            class="flex-1 border border-slate-300 rounded-xl px-4 py-2 text-sm focus:outline-none focus:border-brand"
          />
          <button type="submit" class="bg-brand text-white px-4 py-2 rounded-xl font-semibold flex items-center justify-center hover:bg-brand-dark transition">
            <AppIcon name="paper-airplane" class="size-5" />
          </button>
        </form>
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