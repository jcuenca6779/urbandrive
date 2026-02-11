import { useState } from 'react'
import { X, MapPin, AlertTriangle, Car, Road } from 'lucide-react'
import { apiService } from '../services/api'
import toast from 'react-hot-toast'

const INCIDENT_TYPES = [
  { value: 'Accidente Grave', label: 'Accidente Grave', icon: AlertTriangle, color: 'text-danger-400' },
  { value: 'Tráfico Ligero', label: 'Tráfico Ligero', icon: Car, color: 'text-warning-400' },
  { value: 'Peligro en Vía', label: 'Peligro en Vía', icon: Road, color: 'text-warning-500' },
]

export default function ReportModal({ isOpen, onClose, onSubmit, userId }) {
  const [formData, setFormData] = useState({
    ubicacion: '',
    tipo_incidente: '',
    descripcion: '',
  })
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!formData.ubicacion || !formData.tipo_incidente || !formData.descripcion) {
      toast.error('Por favor completa todos los campos')
      return
    }

    setIsSubmitting(true)
    
    try {
      await apiService.createReport({
        ubicacion: formData.ubicacion,
        tipo_incidente: formData.tipo_incidente,
        descripcion: formData.descripcion,
        usuario_id: userId,
      })
      
      toast.success('Reporte enviado exitosamente')
      setFormData({
        ubicacion: '',
        tipo_incidente: '',
        descripcion: '',
      })
      onClose()
      if (onSubmit) {
        await onSubmit()
      }
    } catch (error) {
      console.error('Error al enviar reporte:', error)
      toast.error('Error al enviar el reporte. Por favor intenta nuevamente.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  if (!isOpen) return null

  return (
    <>
      {/* Overlay */}
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        onClick={onClose}
      >
        {/* Modal */}
        <div 
          className="bg-dark-800 border border-dark-700 rounded-2xl shadow-2xl w-full max-w-md"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-dark-700">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-lg flex items-center justify-center">
                <AlertTriangle className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">Reportar Incidente</h2>
                <p className="text-xs text-dark-400">Ayuda a mejorar el tráfico urbano</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-dark-700 rounded-lg transition-colors"
              aria-label="Cerrar"
            >
              <X className="w-5 h-5 text-dark-400" />
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            {/* Ubicación */}
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">
                <MapPin className="w-4 h-4 inline mr-1" />
                Ubicación
              </label>
              <input
                type="text"
                name="ubicacion"
                value={formData.ubicacion}
                onChange={handleChange}
                placeholder="Ej: Av. Principal 123"
                className="input-field"
                required
              />
            </div>

            {/* Tipo de Incidente */}
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-3">
                Tipo de Incidente
              </label>
              <div className="grid grid-cols-1 gap-3">
                {INCIDENT_TYPES.map((type) => {
                  const Icon = type.icon
                  const isSelected = formData.tipo_incidente === type.value
                  
                  return (
                    <button
                      key={type.value}
                      type="button"
                      onClick={() => setFormData(prev => ({ ...prev, tipo_incidente: type.value }))}
                      className={`
                        flex items-center gap-3 p-4 rounded-lg border-2 transition-all
                        ${isSelected 
                          ? 'border-primary-500 bg-primary-500/10' 
                          : 'border-dark-600 bg-dark-700 hover:border-dark-500'
                        }
                      `}
                    >
                      <div className={`
                        w-10 h-10 rounded-lg flex items-center justify-center
                        ${isSelected ? 'bg-primary-500' : 'bg-dark-600'}
                      `}>
                        <Icon className={`w-5 h-5 ${isSelected ? 'text-white' : type.color}`} />
                      </div>
                      <span className={`font-medium ${isSelected ? 'text-white' : 'text-dark-300'}`}>
                        {type.label}
                      </span>
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Descripción */}
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">
                Descripción
              </label>
              <textarea
                name="descripcion"
                value={formData.descripcion}
                onChange={handleChange}
                placeholder="Describe el incidente en detalle..."
                rows={4}
                className="input-field resize-none"
                required
              />
            </div>

            {/* Botones */}
            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="btn-secondary flex-1"
                disabled={isSubmitting}
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="btn-primary flex-1"
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Enviando...' : 'Enviar Reporte'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </>
  )
}
