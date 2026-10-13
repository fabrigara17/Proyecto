import api from './api'
import { listarTodo } from './paginacion'

// ---- Materias ----
export function getMaterias() {
  return listarTodo('/api/materias/')
}

export async function crearMateria(nombre) {
  const { data } = await api.post('/api/materias/', { nombre })
  return data
}

export async function renombrarMateria(id, nombre) {
  const { data } = await api.patch(`/api/materias/${id}/`, { nombre })
  return data
}

export async function eliminarMateria(id) {
  await api.delete(`/api/materias/${id}/`)
}

// Cada materia en cada curso, con su año de cursada y sus docentes
export async function getResumenMaterias() {
  const { data } = await api.get('/api/plan-estudios/resumen/')
  return data
}

// ---- Cursos ----
export function getCursos() {
  return listarTodo('/api/cursos/')
}

export async function crearCurso(payload) {
  const { data } = await api.post('/api/cursos/', payload)
  return data
}

export async function editarCurso(id, payload) {
  const { data } = await api.patch(`/api/cursos/${id}/`, payload)
  return data
}

export async function eliminarCurso(id) {
  await api.delete(`/api/cursos/${id}/`)
}

// Un curso con sus materias (y docentes), preceptores y alumnos
export async function getDetalleCurso(id) {
  const { data } = await api.get(`/api/cursos/${id}/detalle/`)
  return data
}

// ---- Plan de estudios (materias de un curso) ----
export async function agregarMateriaAlCurso(curso, materia) {
  await api.post('/api/plan-estudios/', { curso, materia })
}

// Agrega varias materias a un curso de una vez (las que ya estaban se ignoran)
export async function agregarMateriasAlCurso(curso, materias) {
  const { data } = await api.post(`/api/cursos/${curso}/agregar-materias/`, { materias })
  return data
}

export async function quitarMateriaDelCurso(id) {
  await api.delete(`/api/plan-estudios/${id}/`)
}

// ---- Docentes de cada materia ----
export async function asignarDocente(materiaCurso, docente) {
  await api.post('/api/asignaciones/', { docente, materia_curso: materiaCurso })
}

export async function quitarDocente(id) {
  await api.delete(`/api/asignaciones/${id}/`)
}

// ---- Preceptores de un curso ----
export async function asignarPreceptor(curso, preceptor) {
  await api.post('/api/asignaciones-preceptor/', { preceptor, curso })
}

export async function quitarPreceptor(id) {
  await api.delete(`/api/asignaciones-preceptor/${id}/`)
}

// ---- Alumnos de un curso ----
export async function inscribirAlumno(curso, alumno) {
  await api.post('/api/inscripciones/', { alumno, curso })
}

export async function desinscribirAlumno(id) {
  await api.delete(`/api/inscripciones/${id}/`)
}

// ---- Familias y alumnos ----
export function getVinculos() {
  return listarTodo('/api/vinculos-familiares/')
}

export async function crearVinculo({ tutor, alumno, parentesco }) {
  const { data } = await api.post('/api/vinculos-familiares/', { tutor, alumno, parentesco })
  return data
}

export async function eliminarVinculo(id) {
  await api.delete(`/api/vinculos-familiares/${id}/`)
}

// Asistencias, aprobación y estadísticas de un curso (equipo de conducción)
export async function getSeguimientoCurso(id) {
  const { data } = await api.get(`/api/cursos/${id}/seguimiento/`)
  return data
}