import { listarTodo } from './paginacion'

export function getCalificaciones() {
  return listarTodo('/api/calificaciones/')
}