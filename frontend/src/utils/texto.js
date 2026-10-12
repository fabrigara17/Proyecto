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