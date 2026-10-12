import api from './api'
import { listarTodo } from './paginacion'

export function getAsistencias() {
  return listarTodo('/api/asistencias/')
}

export async function crearAsistencia(payload) {
  const { data } = await api.post('/api/asistencias/', payload)
  return data
}

// Cursos asignados al usuario (para el preceptor: los suyos)
export async function getCursosAsignados() {
  const { data } = await api.get('/api/cursos/mis-cursos/')
  return data
}

export async function getAlumnosDeCurso(cursoId) {
  const { data } = await api.get(`/api/cursos/${cursoId}/alumnos/`)
  return data
}

// Registros ya cargados de un curso en un día (fecha en formato YYYY-MM-DD)
export function getAsistenciasDelDia(cursoId, fecha) {
  return listarTodo('/api/asistencias/', { curso: cursoId, fecha })
}

// registros: [{ alumno: id, presente: true|false }]
export async function tomarAsistencia({ curso, fecha, registros }) {
  const { data } = await api.post('/api/asistencias/tomar/', { curso, fecha, registros })
  return data
}

// Días sin clases que afectan a un curso en una fecha (los del curso y los de todo el colegio)
export function getDiasSinClases(cursoId, fecha) {
  return listarTodo('/api/dias-sin-clases/', { curso: cursoId, fecha })
}

export async function marcarSinClases({ curso, fecha, motivo, reemplazar }) {
  const { data } = await api.post('/api/dias-sin-clases/', { curso, fecha, motivo, reemplazar })
  return data
}

export async function quitarSinClases(id) {
  await api.delete(`/api/dias-sin-clases/${id}/`)
}