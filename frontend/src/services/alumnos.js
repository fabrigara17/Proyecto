import api from './api'

// Solo para rol FAMILIA: devuelve [{ id, username, first_name, last_name }]
export async function getMisAlumnos() {
  const { data } = await api.get('/api/vinculos-familiares/mis-alumnos/')
  return data
}