// Los DateField del backend llegan como "2026-08-14". new Date() los toma como UTC
// y en Argentina mostraría un día menos, por eso se fuerza la hora local.
function aFecha(valor) {
  return new Date(valor.length === 10 ? `${valor}T00:00:00` : valor)
}

export function nombreCompleto(u) {
  if (!u) return ''
  return `${u.first_name ?? ''} ${u.last_name ?? ''}`.trim() || u.username
}

export function fechaCorta(valor) {
  return aFecha(valor)
    .toLocaleDateString('es-AR', { day: 'numeric', month: 'short' })
    .replace('.', '')
}

export function fechaLarga(valor) {
  return aFecha(valor).toLocaleDateString('es-AR', { weekday: 'long', day: 'numeric', month: 'long' })
}

export function fechaHora(valor) {
  return aFecha(valor).toLocaleString('es-AR', {
    day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
  })
}

export function esReciente(valor, dias = 3) {
  return Date.now() - aFecha(valor).getTime() < dias * 24 * 60 * 60 * 1000
}

export function formatoNota(nota) {
  return Number(nota).toLocaleString('es-AR', { maximumFractionDigits: 2 })
}

export const TIPOS_COMUNICADO = {
  AVISO: 'Aviso',
  COMUNICADO: 'Comunicado',
  ACTIVIDAD: 'Actividad',
  ACTO: 'Acto',
  REUNION: 'Reunión',
}

