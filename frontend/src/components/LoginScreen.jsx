import { useAuth } from '../contexts/AuthContext'
import { MapPin } from 'lucide-react'

export default function LoginScreen() {
  const { login } = useAuth()

  const handleDemoLogin = async () => {
    // Simulación de login - en producción esto sería un formulario real
    await login({ 
      userId: 1, 
      email: 'demo@urbandrive.com', 
      name: 'Usuario Demo' 
    })
  }

  return (
    <div className="h-screen w-screen flex items-center justify-center bg-dark-950">
      <div className="text-center max-w-md mx-auto px-6">
        <div className="w-20 h-20 bg-gradient-to-br from-primary-500 to-primary-600 rounded-2xl flex items-center justify-center shadow-lg shadow-primary-500/30 mx-auto mb-6">
          <MapPin className="w-10 h-10 text-white" />
        </div>
        <h1 className="text-3xl font-bold text-white mb-2">UrbanDrive</h1>
        <p className="text-dark-400 mb-8">Sistema de Reportes Inteligente</p>
        <p className="text-dark-500 mb-6">Por favor inicia sesión para continuar</p>
        <button
          onClick={handleDemoLogin}
          className="btn-primary w-full"
        >
          Iniciar Sesión (Demo)
        </button>
        <p className="text-xs text-dark-600 mt-4">
          Nota: Esta es una versión de demostración. En producción se requeriría autenticación real.
        </p>
      </div>
    </div>
  )
}
