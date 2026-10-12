<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAlumnosStore } from '@/stores/alumnos'
import { logout as logoutApi } from '@/services/auth'
import { nombreCompleto } from '@/utils/formato'
import AppIcon from '@/components/AppIcon.vue'

const auth = useAuthStore()
const alumnos = useAlumnosStore()
const router = useRouter()

const usuario = computed(() => auth.usuario)
const iniciales = computed(() => {
  const u = usuario.value
  const a = u.first_name?.[0] ?? u.username[0]
  const b = u.last_name?.[0] ?? ''
  return (a + b).toUpperCase()
})

onMounted(() => {
  alumnos.cargar(auth.rol).catch(() => {})
})

async function cerrarSesion() {
  try {
    await logoutApi() // invalida el token en el servidor
  } catch {
    // aunque falle, cerramos la sesión localmente
  }
  alumnos.reset()
  auth.cerrarSesion()
  router.push('/login')
}
</script>

<template>
  <div v-if="usuario" class="pagina">
    <h1 class="titulo-pagina">Mi perfil</h1>

    <div class="mt-5 max-w-md rounded-3xl bg-white p-6 shadow-sm ring-1 ring-slate-100">
      <div class="flex items-center gap-4">
        <span class="grid size-16 shrink-0 place-items-center rounded-full bg-brand text-2xl font-extrabold text-white">
          {{ iniciales }}
        </span>
        <div class="min-w-0">
          <p class="truncate text-lg font-extrabold text-slate-900">{{ nombreCompleto(usuario) }}</p>
          <p class="text-sm font-semibold text-brand">{{ usuario.rol_display }}</p>
        </div>
      </div>

      <dl class="mt-6 space-y-3 text-sm">
        <div class="flex justify-between gap-4">
          <dt class="text-slate-500">Usuario</dt>
          <dd class="font-semibold">{{ usuario.username }}</dd>
        </div>
        <div class="flex justify-between gap-4">
          <dt class="text-slate-500">Email</dt>
          <dd class="truncate font-semibold">{{ usuario.email || '—' }}</dd>
        </div>
        <div v-if="alumnos.lista.length" class="flex justify-between gap-4">
          <dt class="text-slate-500">Alumnos a cargo</dt>
          <dd class="text-right font-semibold">
            <span v-for="a in alumnos.lista" :key="a.id" class="block">{{ nombreCompleto(a) }}</span>
          </dd>
        </div>
      </dl>
    </div>

    <button
      type="button"
      @click="cerrarSesion"
      class="mt-5 flex w-full max-w-md items-center justify-center gap-2 rounded-2xl border border-red-200 bg-white py-3 font-bold text-red-600 hover:bg-red-50"
    >
      <AppIcon name="logout" class="size-5" />
      Cerrar sesión
    </button>
  </div>
</template>