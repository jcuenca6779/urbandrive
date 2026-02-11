import { useState, useEffect } from 'react'
import { Toaster } from 'react-hot-toast'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import MapComponent from './components/MapComponent'
import GamificationPanel from './components/GamificationPanel'
import ReportModal from './components/ReportModal'
import LoginScreen from './components/LoginScreen'
import { apiService } from './services/api'
import { MapPin } from 'lucide-react'

function AppContent() {
  const { user, isAuthenticated, loadUserProfile } = useAuth()
  const [userProfile, setUserProfile] = useState(null)
  const [reports, setReports] = useState([])
  const [isReportModalOpen, setIsReportModalOpen] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (isAuthenticated && user) {
      loadData()
    } else {
      // Si no está autenticado, mostrar mensaje o redirigir
      setLoading(false)
    }
  }, [isAuthenticated, user])

  const loadData = async () => {
    await Promise.all([
      loadUserProfileData(),
      loadReports()
    ])
  }

  const loadUserProfileData = async () => {
    try {
      if (user?.id) {
        const profile = await apiService.getUserProfile(user.id)
        setUserProfile(profile)
      }
    } catch (error) {
      console.error('Error cargando perfil:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadReports = async () => {
    try {
      const data = await apiService.getReports()
      setReports(data)
    } catch (error) {
      console.error('Error cargando reportes:', error)
    }
  }

  const handleReportSubmitted = async () => {
    await loadReports()
    await loadUserProfileData() // Recargar perfil para actualizar XP
  }

  // Si no está autenticado, mostrar mensaje
  if (!isAuthenticated) {
    return (
      <LoginScreen />
    )
  }

  return (
    <div className="h-screen w-screen overflow-hidden bg-dark-950">
      <Toaster 
        position="top-right"
        toastOptions={{
          className: 'bg-dark-800 text-dark-100 border border-dark-700',
          success: {
            iconTheme: {
              primary: '#22c55e',
              secondary: '#fff',
            },
          },
          error: {
            iconTheme: {
              primary: '#ef4444',
              secondary: '#fff',
            },
          },
        }}
      />
      
      {/* Header con logo y título */}
      <header className="absolute top-0 left-0 right-0 z-50 bg-dark-900/95 backdrop-blur-sm border-b border-dark-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-lg flex items-center justify-center shadow-lg shadow-primary-500/30">
              <MapPin className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">UrbanDrive</h1>
              <p className="text-xs text-dark-400">Sistema de Reportes Inteligente</p>
            </div>
          </div>
          
          {/* Panel de Gamificación en el header */}
          <GamificationPanel 
            profile={userProfile} 
            loading={loading}
          />
        </div>
      </header>

      {/* Mapa principal */}
      <div className="pt-20 h-full">
        <MapComponent reports={reports} />
      </div>

      {/* Botón flotante para reportar */}
      <button
        onClick={() => setIsReportModalOpen(true)}
        className="fixed bottom-8 right-8 z-50 w-16 h-16 bg-gradient-to-br from-primary-500 to-primary-600 rounded-full shadow-2xl shadow-primary-500/50 flex items-center justify-center text-white hover:scale-110 transition-transform duration-200 group"
        aria-label="Reportar incidente"
      >
        <span className="text-3xl font-bold group-hover:rotate-90 transition-transform duration-200">+</span>
      </button>

      {/* Modal de reporte */}
      <ReportModal
        isOpen={isReportModalOpen}
        onClose={() => setIsReportModalOpen(false)}
        onSubmit={handleReportSubmitted}
        userId={user?.id}
      />
    </div>
  )
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}

export default App
