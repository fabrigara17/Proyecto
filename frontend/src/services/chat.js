import api from './api'
import { listarTodo } from './paginacion'

export default {
  obtenerConversaciones() {
    return listarTodo('/api/conversaciones/')
  },
  crearConversacion(data) {
    return api.post('/api/conversaciones/', data)
  },
  obtenerMensajes(conversacionId) {
    return listarTodo('/api/mensajes/', { conversacion: conversacionId })
  },
  // Siempre multipart: sirve tanto para texto solo como para texto + archivo
  enviarMensaje({ conversacion, texto = '', archivo = null }) {
    const form = new FormData()
    form.append('conversacion', conversacion)
    form.append('texto', texto)
    if (archivo) form.append('archivo', archivo)
    return api.post('/api/mensajes/', form)
  },
  obtenerUsuariosDisponibles(rol = 'todos') {
    return api.get('/api/conversaciones/usuarios_disponibles/', { params: { rol } })
  },
  async descargarAdjunto(mensaje) {
    const { data } = await api.get(`/api/mensajes/${mensaje.id}/descargar/`, {
      responseType: 'blob',
    })
    const url = URL.createObjectURL(data)
    const a = document.createElement('a')
    a.href = url
    a.download = mensaje.archivo_nombre
    document.body.appendChild(a)
    a.click()
    a.remove()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  },
}