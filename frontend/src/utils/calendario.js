// Tipos de evento y su color (los de la leyenda de la referencia)
export const TIPOS_EVENTO = [
  { valor: 'EVENTO', texto: 'Evento', fondo: 'bg-green-400', suave: 'bg-green-100 text-green-800' },
  { valor: 'EXAMEN', texto: 'Examen', fondo: 'bg-pink-400', suave: 'bg-pink-100 text-pink-800' },
  { valor: 'REUNION', texto: 'Reunión', fondo: 'bg-cyan-300', suave: 'bg-cyan-100 text-cyan-800' },
  { valor: 'AVISO', texto: 'Aviso', fondo: 'bg-yellow-300', suave: 'bg-yellow-100 text-yellow-800' },
]
export const TIPO_POR_VALOR = Object.fromEntries(TIPOS_EVENTO.map((t) => [t.valor, t]))

export const DIAS = [
  { corto: 'L', largo: 'Lunes' },
  { corto: 'M', largo: 'Martes' },
  { corto: 'M', largo: 'Miércoles' },
  { corto: 'J', largo: 'Jueves' },
  { corto: 'V', largo: 'Viernes' },
  { corto: 'S', largo: 'Sábado' },
  { corto: 'D', largo: 'Domingo' },
]

// Las fechas se manejan como texto YYYY-MM-DD, siempre en hora local
export function aISO(d) {
  const mes = String(d.getMonth() + 1).padStart(2, '0')
  const dia = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${mes}-${dia}`
}

export function desdeISO(iso) {
  const [anio, mes, dia] = iso.split('-').map(Number)
  return new Date(anio, mes - 1, dia)
}

export function sumarDias(iso, n) {
  const d = desdeISO(iso)
  d.setDate(d.getDate() + n)
  return aISO(d)
}

// Semanas (de lunes a domingo) que cubren un mes. mes0: 0 a 11
export function semanasDelMes(anio, mes0) {
  const primero = new Date(anio, mes0, 1)
  const ultimo = new Date(anio, mes0 + 1, 0)
  const cursor = new Date(anio, mes0, 1 - ((primero.getDay() + 6) % 7)) // lunes anterior o igual al 1
  const hoy = aISO(new Date())
  const semanas = []
  while (cursor <= ultimo) {
    const semana = []
    for (let i = 0; i < 7; i++) {
      semana.push({
        iso: aISO(cursor),
        numero: cursor.getDate(),
        delMes: cursor.getMonth() === mes0,
        esHoy: aISO(cursor) === hoy,
      })
      cursor.setDate(cursor.getDate() + 1)
    }
    semanas.push(semana)
  }
  return semanas
}

export function nombreMes(anio, mes0) {
  return `${new Date(anio, mes0, 1).toLocaleDateString('es-AR', { month: 'long' })} ${anio}`
}

// Sin hora (todo el día) primero, después por hora y por título
export function compararEventos(a, b) {
  const ha = a.hora_inicio ?? ''
  const hb = b.hora_inicio ?? ''
  if (ha !== hb) return ha < hb ? -1 : 1
  return a.titulo.localeCompare(b.titulo, 'es')
}

// { 'YYYY-MM-DD': [eventos] } para el rango visible; un evento de varios días aparece en cada uno
export function eventosPorDia(eventos, desde, hasta) {
  const mapa = {}
  for (const e of eventos) {
    let dia = e.fecha_inicio < desde ? desde : e.fecha_inicio
    const fin = e.fecha_fin > hasta ? hasta : e.fecha_fin
    while (dia <= fin) {
      ;(mapa[dia] ??= []).push(e)
      dia = sumarDias(dia, 1)
    }
  }
  for (const lista of Object.values(mapa)) lista.sort(compararEventos)
  return mapa
}

export function horaCorta(hora) {
  return hora ? hora.slice(0, 5) : ''
}