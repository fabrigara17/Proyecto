import api from './api'

export async function getEventos(desde, hasta) {
  const { data } = await api.get('/api/eventos/', { params: { desde, hasta } })
  return data
}

// Lo que esta persona puede elegir como destinatarios
export async function getOpcionesEvento() {
  const { data } = await api.get('/api/eventos/opciones/')
  return data
}

// { total, detalle: [{ texto, cantidad }] }
export async function previsualizarDestinatarios(destinos) {
  const { data } = await api.post('/api/eventos/destinatarios/', { destinos })
  return data
}

export async function crearEvento(payload) {
  const { data } = await api.post('/api/eventos/', payload)
  return data
}

export async function editarEvento(id, payload) {
  const { data } = await api.patch(`/api/eventos/${id}/`, payload)
  return data
}

export async function eliminarEvento(id) {
  await api.delete(`/api/eventos/${id}/`)
}