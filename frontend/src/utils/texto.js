// Texto sin tildes ni mayúsculas, para comparar en las búsquedas
export function normalizar(texto) {
  return String(texto ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
}

export function anioCursada(n) {
  return n ? `${n}º año` : 'Sin año de cursada'
}

// "Hace 5 min", "Hace 3 h", "Hace 2 días" o la fecha. Sin valor: nunca se conectó
export function haceCuanto(valor) {
  if (!valor) return 'Nunca se conectó'
  const fecha = new Date(valor)
  const minutos = Math.floor((Date.now() - fecha.getTime()) / 60000)
  if (minutos < 1) return 'Hace un momento'
  if (minutos < 60) return `Hace ${minutos} min`
  const horas = Math.floor(minutos / 60)
  if (horas < 24) return `Hace ${horas} h`
  const dias = Math.floor(horas / 24)
  if (dias < 30) return `Hace ${dias} ${dias === 1 ? 'día' : 'días'}`
  return fecha.toLocaleDateString('es-AR', { day: 'numeric', month: 'short', year: 'numeric' })
}

// Turnos de los cursos
export const TURNOS = [
  { valor: 'MANANA', texto: 'Turno mañana' },
  { valor: 'TARDE', texto: 'Turno tarde' },
  { valor: 'VESPERTINO', texto: 'Turno vespertino' },
]

export const COLOR_TURNO = {
  MANANA: 'bg-amber-100 text-amber-700',
  TARDE: 'bg-orange-100 text-orange-700',
  VESPERTINO: 'bg-indigo-100 text-indigo-700',
}

export function nombreTurno(valor) {
  return TURNOS.find((t) => t.valor === valor)?.texto ?? 'Sin turno'
}

// 91.3 -> "91,3%". Sin dato: "—"
export function porcentaje(n) {
  if (n === null || n === undefined) return '—'
  return `${n.toLocaleString('es-AR', { maximumFractionDigits: 1 })}%`
}

// "2026-10" -> "oct 2026"
export function etiquetaMes(ym) {
  const [anio, mes] = ym.split('-').map(Number)
  return new Date(anio, mes - 1, 1).toLocaleDateString('es-AR', { month: 'short', year: 'numeric' })
}