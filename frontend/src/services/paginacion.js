import api from './api'

// Recorre todas las páginas de un listado paginado de DRF y devuelve un array.
// Si el endpoint no pagina (devuelve un array directo), lo devuelve tal cual.
export async function listarTodo(url, params = {}) {
  const items = []
  let page = 1
  while (true) {
    const { data } = await api.get(url, { params: { ...params, page } })
    if (Array.isArray(data)) return data
    items.push(...data.results)
    if (!data.next) break
    page++
  }
  return items
}