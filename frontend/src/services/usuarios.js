import api from './api'
import { listarTodo } from './paginacion'

// params opcionales, por ejemplo { rol: 'DOCENTE' }
export function getUsuarios(params = {}) {
  return listarTodo('/api/usuarios/', params)
}

export async function crearUsuario(payload) {
  const { data } = await api.post('/api/usuarios/', payload)
  return data
}