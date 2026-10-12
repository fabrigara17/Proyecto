import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
})

api.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.token) {
    config.headers.Authorization = `Token ${auth.token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (error) => {
    const auth = useAuthStore()
    // Token inválido o vencido: limpiamos la sesión y volvemos al login
    if (error.response?.status === 401 && auth.token) {
      auth.cerrarSesion()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

export default api