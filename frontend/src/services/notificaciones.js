import api from './api'
import { listarTodo } from './paginacion'

export function getNotificaciones() {
  return listarTodo('/api/notificaciones/')
}

export async function getCantidadNoLeidas() {
  const { data } = await api.get('/api/notificaciones/no-leidas/')
  return data.cantidad
}

export async function marcarLeida(id) {
  const { data } = await api.patch(`/api/notificaciones/${id}/`, { leida: true })
  return data
}

export async function marcarTodasLeidas() {
  const { data } = await api.post('/api/notificaciones/marcar-todas-leidas/')
  return data
}