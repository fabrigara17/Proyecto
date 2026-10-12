// Convierte la respuesta de error de DRF (que puede venir anidada) en un solo texto
export function mensajeError(e, porDefecto = 'Ocurrió un error. Probá de nuevo.') {
  if (!e.response) return 'No se pudo conectar con el servidor.'
  const textos = []
  const recorrer = (v) => {
    if (typeof v === 'string') textos.push(v)
    else if (Array.isArray(v)) v.forEach(recorrer)
    else if (v && typeof v === 'object') Object.values(v).forEach(recorrer)
  }
  recorrer(e.response.data)
  return textos.join(' ') || porDefecto
}