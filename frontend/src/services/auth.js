import api from './api'

export async function login(username, password) {
  const { data } = await api.post('/api/auth/login/', { username, password })
  return data
}

export async function logout() {
  await api.post('/api/auth/logout/')
}

export async function getPerfil() {
  const { data } = await api.get('/api/auth/perfil/')
  return data
}

export async function cambiarPassword(passwordActual, passwordNueva) {
  const { data } = await api.post('/api/auth/cambiar-password/', {
    password_actual: passwordActual,
    password_nueva: passwordNueva,
  })
  return data
}