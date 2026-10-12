<script setup>
import { fechaCorta, esReciente, TIPOS_COMUNICADO } from '@/utils/formato'

defineProps({
  comunicado: { type: Object, required: true },
  completo: { type: Boolean, default: false },
})
</script>

<template>
  <article class="rounded-2xl border border-blue-100 bg-white p-4 shadow-sm">
    <div class="flex items-center justify-between gap-2 text-xs text-slate-500">
      <span class="truncate">{{ comunicado.autor || 'Institución' }}</span>
      <span class="flex shrink-0 items-center gap-2">
        <span class="text-slate-400">{{ fechaCorta(comunicado.fecha_publicacion) }}</span>
        <span
          v-if="esReciente(comunicado.fecha_publicacion)"
          class="rounded-full bg-red-100 px-2 py-0.5 font-bold text-red-500"
        >Nuevo</span>
      </span>
    </div>

    <h3 class="mt-2 font-bold text-slate-900">{{ comunicado.titulo }}</h3>
    <p
      class="mt-1 text-sm text-slate-500"
      :class="completo ? 'whitespace-pre-line' : 'line-clamp-2'"
    >{{ comunicado.contenido }}</p>

    <span
      v-if="completo"
      class="mt-3 inline-block rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-bold text-brand"
    >{{ TIPOS_COMUNICADO[comunicado.tipo] ?? comunicado.tipo }}</span>
  </article>
</template>