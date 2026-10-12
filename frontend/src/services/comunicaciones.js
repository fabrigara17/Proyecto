import api from './api'
import { listarTodo } from './paginacion'

export function getComunicaciones() {
  return listarTodo('/api/comunicaciones/')
}

// Solo la primera página (ya viene ordenada de más nueva a más vieja)
export async function getComunicacionesRecientes(cantidad = 3) {
  const { data } = await api.get('/api/comunicaciones/')
  return data.results.slice(0, cantidad)
}

export async function crearComunicacion({ titulo, contenido, tipo }) {
  const { data } = await api.post('/api/comunicaciones/', { titulo, contenido, tipo })
  return data
}

export async function eliminarComunicacion(id) {
  await api.delete(`/api/comunicaciones/${id}/`)
}

// Registra que el usuario abrió estos comunicados
export async function marcarVistas(ids) {
  await api.post('/api/comunicaciones/marcar-vistas/', { ids })
}

// Solo administrador: quién lo vio y quién no
export async function getVistas(id) {
  const { data } = await api.get(`/api/comunicaciones/${id}/vistas/`)
  return data
}