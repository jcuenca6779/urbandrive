import { createContext, useContext, useState, useEffect } from 'react'
import { setAuthToken, getAuthToken } from '../services/api'
import { apiService } from '../services/api'
import toast from 'react-hot-toast'

const AuthContext = createContext(null)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth debe ser usado dentro de un AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [token, setTokenState] = useState(null)
  const [loading, setLoading] = useState(true)
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  // Cargar token y datos del usuario al iniciar
  useEffect(() => {
    const storedToken = getAuthToken()
    const storedUser = localStorage.getItem('user_data')
    
    if (storedToken) {
      setTokenState(storedToken)
      setAuthToken(storedToken)
      
      if (storedUser) {
        try {
          setUser(JSON.parse(storedUser))
          setIsAuthenticated(true)
        } catch (error) {
          console.error('Error al parsear datos de usuario:', error)
          localStorage.removeItem('user_data')
        }
      }
    }
    
    setLoading(false)
  }, [])

  // Función de login
  const login = async (credentials) => {
    try {
      // Aquí harías la petición al servicio de autenticación
      // Por ahora simulamos una respuesta
      // En producción esto sería: const response = await apiService.login(credentials)
      
      // Simulación temporal - reemplazar con llamada real al auth-service
      const mockResponse = {
        token: 'mock_jwt_token_' + Date.now(),
        user: {
          id: credentials.userId || 1,
          email: credentials.email || 'user@example.com',
          name: credentials.name || 'Usuario Demo'
        }
      }
      
      const { token: newToken, user: userData } = mockResponse
      
      // Guardar token y datos del usuario
      setTokenState(newToken)
      setAuthToken(newToken)
      setUser(userData)
      setIsAuthenticated(true)
      localStorage.setItem('user_data', JSON.stringify(userData))
      
      toast.success('Sesión iniciada correctamente')
      
      return { success: true, user: userData }
    } catch (error) {
      console.error('Error en login:', error)
      toast.error('Error al iniciar sesión')
      return { success: false, error: error.message }
    }
  }

  // Función de logout
  const logout = () => {
    setTokenState(null)
    setUser(null)
    setIsAuthenticated(false)
    setAuthToken(null)
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_data')
    
    toast.success('Sesión cerrada')
  }

  // Función para actualizar el token (útil si se renueva automáticamente)
  const updateToken = (newToken) => {
    setTokenState(newToken)
    setAuthToken(newToken)
  }

  // Función para obtener el perfil del usuario autenticado
  const loadUserProfile = async () => {
    if (!isAuthenticated || !user) return null
    
    try {
      const profile = await apiService.getUserProfile(user.id)
      return profile
    } catch (error) {
      console.error('Error al cargar perfil:', error)
      return null
    }
  }

  const value = {
    user,
    token,
    loading,
    isAuthenticated,
    login,
    logout,
    updateToken,
    loadUserProfile,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export default AuthContext
