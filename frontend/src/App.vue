<script setup>
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import NavPrincipal from '@/components/NavPrincipal.vue'
import logo from '@/assets/logo.png'

const auth = useAuthStore()

const conNav = computed(
  () => auth.estaAutenticado && !!auth.usuario && !auth.debeCambiarPassword,
)
</script>

<template>
  <div class="min-h-dvh md:flex">
    <NavPrincipal v-if="conNav" />
    <main class="min-w-0 flex-1" :class="{ 'pb-24 md:pb-0': conNav }">
      <header
        v-if="conNav"
        class="sticky top-0 z-10 flex items-center gap-2 border-b border-slate-200 bg-white/90 px-4 py-2 backdrop-blur md:hidden"
      >
        <img :src="logo" alt="" class="size-8" />
        <span class="text-lg font-extrabold text-brand-dark">Libreta Digital</span>
      </header>

      <router-view />
    </main>
  </div>
</template>