import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getPerfil } from '@/services/auth'
import InicioView from '../views/InicioView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    { path: '/', name: 'inicio', component: InicioView },
    { path: '/login', name: 'login', component: () => import('../views/LoginView.vue') },
    { path: '/cambiar-password', name: 'cambiar-password', component: () => import('../views/CambiarPasswordView.vue') },
    { path: '/comunicados', name: 'comunicados', component: () => import('../views/ComunicadosView.vue') },
    {
      path: '/historial',
      name: 'historial',
      component: () => import('../views/HistorialView.vue'),
      meta: { excluir: ['PRECEPTOR', 'ADMIN', 'CONDUCCION'] },
    },
    { path: '/notificaciones', name: 'notificaciones', component: () => import('../views/NotificacionesView.vue') },
    { path: '/perfil', name: 'perfil', component: () => import('../views/PerfilView.vue') },
    { path: '/materiales', name: 'materiales', component: () => import('../views/MaterialesView.vue') },
    {
      path: '/asistencias',
      name: 'asistencias',
      component: () => import('../views/AsistenciasView.vue'),
      meta: { roles: ['PRECEPTOR'] },
    },
    {
      path: '/asistencias/:cursoId',
      name: 'asistencia-curso',
      component: () => import('../views/AsistenciaCursoView.vue'),
      meta: { roles: ['PRECEPTOR'] },
    },
    {
      path: '/usuarios',
      name: 'usuarios',
      component: () => import('../views/UsuariosView.vue'),
      meta: { roles: ['ADMIN'] },
    },
        {
      path: '/materias',
      name: 'materias',
      component: () => import('../views/MateriasView.vue'),
      meta: { roles: ['ADMIN', 'CONDUCCION'] },
    },
    {
      path: '/cursos',
      name: 'cursos',
      component: () => import('../views/CursosView.vue'),
      meta: { roles: ['ADMIN', 'CONDUCCION'] },
    },
    {
      path: '/cursos/:id',
      name: 'curso-detalle',
      component: () => import('../views/CursoDetalleView.vue'),
      meta: { roles: ['ADMIN', 'CONDUCCION'] },
    },
    {
      path: '/equipo',
      name: 'equipo',
      component: () => import('../views/EquipoView.vue'),
      meta: { roles: ['ADMIN', 'CONDUCCION'] },
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  if (!auth.estaAutenticado) {
    return to.name === 'login' ? true : { name: 'login' }
  }

  // Si recargó la página hay token pero todavía no tenemos los datos del usuario
  if (!auth.usuario) {
    try {
      auth.setUsuario(await getPerfil())
    } catch {
      auth.cerrarSesion()
      return { name: 'login' }
    }
  }

  if (auth.debeCambiarPassword) {
    return to.name === 'cambiar-password' ? true : { name: 'cambiar-password' }
  }

  if (to.name === 'login' || to.name === 'cambiar-password') {
    return { name: 'inicio' }
  }

  // Pantallas solo para ciertos roles, o vedadas para ciertos roles
  if (to.meta.roles && !to.meta.roles.includes(auth.rol)) {
    return { name: 'inicio' }
  }
  if (to.meta.excluir?.includes(auth.rol)) {
    return { name: 'inicio' }
  }

  return true
})

export default router