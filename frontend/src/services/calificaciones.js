import api from './api'
import { listarTodo } from './paginacion'

// params opcionales, por ejemplo { curso: 1, materia: 2, etapa: 3 }
export function getCalificaciones(params = {}) {
  return listarTodo('/api/calificaciones/', params)
}

// payload: { alumno, materia, curso, etapa, nota, detalle }
export async function crearCalificacion(payload) {
  const { data } = await api.post('/api/calificaciones/', payload)
  return data
}

export async function editarCalificacion(id, payload) {
  const { data } = await api.patch(`/api/calificaciones/${id}/`, payload)
  return data
}

export async function eliminarCalificacion(id) {
  await api.delete(`/api/calificaciones/${id}/`)
}

// ---- Etapas (períodos en los que se pueden cargar notas) ----
export async function getEtapas(anioLectivo) {
  const params = anioLectivo ? { anio_lectivo: anioLectivo } : {}
  const { data } = await api.get('/api/etapas/', { params })
  return data
}

// payload: { nombre, anio_lectivo, fecha_inicio, fecha_fin }
export async function crearEtapa(payload) {
  const { data } = await api.post('/api/etapas/', payload)
  return data
}

export async function editarEtapa(id, payload) {
  const { data } = await api.patch(`/api/etapas/${id}/`, payload)
  return data
}

export async function eliminarEtapa(id) {
  await api.delete(`/api/etapas/${id}/`)
}