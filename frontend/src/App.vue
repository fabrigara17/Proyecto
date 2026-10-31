<script setup>
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useMenuLateral } from '@/composables/menuLateral'
import NavPrincipal from '@/components/NavPrincipal.vue'
import AppIcon from '@/components/AppIcon.vue'
import logo from '@/assets/logo.png'

const auth = useAuthStore()
const menu = useMenuLateral()

const conNav = computed(
  () => auth.estaAutenticado && !!auth.usuario && !auth.debeCambiarPassword,
)
</script>

<template>
  <div class="min-h-dvh md:flex">
    <NavPrincipal v-if="conNav" />
    <main class="min-w-0 flex-1">
      <header
        v-if="conNav"
        class="sticky top-0 z-10 flex items-center gap-2 border-b border-slate-200 bg-white/90 px-2 py-2 backdrop-blur md:hidden"
      >
        <button
          type="button"
          @click="menu.abrir()"
          aria-label="Abrir menú"
          aria-controls="menu-lateral"
          :aria-expanded="menu.abierto.value"
          class="grid size-10 place-items-center rounded-md text-slate-600 transition-colors hover:bg-slate-100 active:bg-slate-200"
        >
          <AppIcon name="bars-3" class="size-6" />
        </button>
        <img :src="logo" alt="" class="size-8" />
        <span class="text-lg font-semibold tracking-tight text-brand-dark">Libreta Digital</span>
      </header>

      <router-view v-slot="{ Component }">
        <Transition name="pagina" mode="out-in">
          <component :is="Component" />
        </Transition>
      </router-view>
    </main>
  </div>
</template>