import api from './api'
import { listarTodo } from './paginacion'

export function getAsistencias() {
  return listarTodo('/api/asistencias/')
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

// ---- Horario semanal ----

// Materias de los cursos del usuario (cada una con su id de plan: "materia_curso"). Sirven para armar el horario
export async function getMateriasDeMisCursos() {
  const { data } = await api.get('/api/plan-estudios/mis-materias/')
  return data
}

// Clases del horario de un curso. diaSemana opcional: 0 = lunes ... 4 = viernes
export async function getHorarios(cursoId, diaSemana) {
  const params = { curso: cursoId }
  if (diaSemana !== undefined) params.dia_semana = diaSemana
  const { data } = await api.get('/api/horarios/', { params })
  return data
}

// payload: { curso, materia_curso, dia_semana, hora_inicio: 'HH:MM', hora_fin: 'HH:MM' }
export async function crearClase(payload) {
  const { data } = await api.post('/api/horarios/', payload)
  return data
}

export async function eliminarClase(id) {
  await api.delete(`/api/horarios/${id}/`)
}

// ---- Asistencia por clase ----

// Registros ya cargados de una clase en un día (fecha en formato YYYY-MM-DD)
export function getAsistenciasDeClase(claseId, fecha) {
  return listarTodo('/api/asistencias/', { clase: claseId, fecha })
}

// registros: [{ alumno: id, estado: 'PRESENTE' | 'AUSENTE' | 'TARDE' | 'RETIRO' }]
export async function tomarAsistencia({ clase, fecha, registros }) {
  const { data } = await api.post('/api/asistencias/tomar/', { clase, fecha, registros })
  return data
}

// ---- Días sin clases ----

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