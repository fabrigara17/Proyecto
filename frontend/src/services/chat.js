import api from './api';

export default {
  obtenerConversaciones() {
    return api.get('/conversaciones/');
  },
  crearConversacion(data) {
    return api.post('/conversaciones/', data);
  },
  obtenerMensajes(conversacionId) {
    return api.get(`/mensajes/?conversacion=${conversacionId}`);
  },
  enviarMensaje(data) {
    return api.post('/mensajes/', data);
  }
};