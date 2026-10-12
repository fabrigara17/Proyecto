import api from './api'
import { listarTodo } from './paginacion'

export function getMateriales() {
  return listarTodo('/api/materiales/')
}

// Materias y cursos que puede usar el docente para subir material
export async function getMisMaterias() {
  const { data } = await api.get('/api/plan-estudios/mis-materias/')
  return data
}

export async function subirMaterial({ titulo, descripcion, materiaCurso, archivo }) {
  const form = new FormData()
  form.append('titulo', titulo)
  form.append('descripcion', descripcion)
  form.append('materia_curso', materiaCurso)
  form.append('archivo', archivo)
  const { data } = await api.post('/api/materiales/', form)
  return data
}

export async function eliminarMaterial(id) {
  await api.delete(`/api/materiales/${id}/`)
}

export async function getConsultas(materialId) {
  const { data } = await api.get(`/api/materiales/${materialId}/consultas/`)
  return data
}

export async function enviarConsulta(materialId, texto) {
  const { data } = await api.post(`/api/materiales/${materialId}/consultas/`, { texto })
  return data
}

export async function descargarMaterial(material) {
  const { data } = await api.get(`/api/materiales/${material.id}/descargar/`, {
    responseType: 'blob',
  })
  const url = URL.createObjectURL(data)
  const a = document.createElement('a')
  a.href = url
  a.download = material.archivo_nombre
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}