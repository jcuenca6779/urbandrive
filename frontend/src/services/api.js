import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost/api'

// Crear instancia de Axios configurada para el API Gateway
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 segundos de timeout
})

// Función para obtener el token del localStorage
const getToken = () => {
  return localStorage.getItem('auth_token')
}

// Interceptor de solicitudes: agrega el token JWT a todas las peticiones
api.interceptors.request.use(
  (config) => {
    const token = getToken()
    
    // Agregar token JWT al header Authorization si existe
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Interceptor de respuestas: maneja errores de autenticación
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    // Si el token es inválido o expiró, limpiar y redirigir al login
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user_data')
      
      // Redirigir al login si no estamos ya ahí
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    
    return Promise.reject(error)
  }
)

// Función para establecer el token (usada por AuthContext)
export const setAuthToken = (token) => {
  if (token) {
    localStorage.setItem('auth_token', token)
  } else {
    localStorage.removeItem('auth_token')
  }
}

// Función para obtener el token actual
export const getAuthToken = () => {
  return getToken()
}

export const apiService = {
  // Reportes de tráfico
  async getReports() {
    const response = await api.get('/traffic/reportes')
    return response.data
  },

  async createReport(reportData) {
    const response = await api.post('/traffic/reportes', reportData)
    return response.data
  },

  async getReportById(id) {
    const response = await api.get(`/traffic/reportes/${id}`)
    return response.data
  },

  // Gamificación
  async getUserProfile(userId) {
    const response = await api.get(`/gamification/profile/${userId}`)
    return response.data
  },

  async getLeaderboard(limit = 10) {
    const response = await api.get(`/gamification/leaderboard?limit=${limit}`)
    return response.data
  },

  // AI Service
  async classifyIncident(description) {
    const response = await api.post('/ai/clasificar-incidente', {
      descripcion: description
    })
    return response.data
  },
}

export default api
