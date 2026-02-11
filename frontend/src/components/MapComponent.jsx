import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import { useEffect } from 'react'
import L from 'leaflet'
import { AlertTriangle, Car, Road, MapPin } from 'lucide-react'

// Fix para iconos de Leaflet en Vite
import icon from 'leaflet/dist/images/marker-icon.png'
import iconShadow from 'leaflet/dist/images/marker-shadow.png'
import iconRetina from 'leaflet/dist/images/marker-icon-2x.png'

let DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconRetinaUrl: iconRetina,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
})

L.Marker.prototype.options.icon = DefaultIcon

// Componente para centrar el mapa en la ubicación del usuario
function MapController({ center }) {
  const map = useMap()
  
  useEffect(() => {
    if (center) {
      map.setView(center, 13)
    }
  }, [center, map])
  
  return null
}

// Función para obtener el icono según el tipo de incidente
const getIncidentIcon = (tipo) => {
  const iconConfig = {
    'Accidente Grave': {
      icon: '🚨',
      color: '#ef4444',
      bgColor: '#dc2626'
    },
    'Tráfico Ligero': {
      icon: '🚗',
      color: '#f59e0b',
      bgColor: '#d97706'
    },
    'Peligro en Vía': {
      icon: '⚠️',
      color: '#fbbf24',
      bgColor: '#f59e0b'
    }
  }
  
  return iconConfig[tipo] || iconConfig['Peligro en Vía']
}

// Función para obtener el color según la severidad
const getSeverityColor = (severidad) => {
  const colors = {
    'critica': '#dc2626',
    'alta': '#ef4444',
    'media': '#f59e0b',
    'baja': '#22c55e'
  }
  return colors[severidad] || colors['media']
}

export default function MapComponent({ reports = [] }) {
  // Coordenadas por defecto (puedes cambiar esto a la ubicación del usuario)
  const defaultCenter = [-12.0464, -77.0428] // Lima, Perú (ejemplo)
  
  // Crear iconos personalizados para cada tipo de incidente
  const createCustomIcon = (tipo, severidad) => {
    const incident = getIncidentIcon(tipo)
    const severityColor = getSeverityColor(severidad)
    
    return L.divIcon({
      className: 'custom-marker',
      html: `
        <div style="
          background: linear-gradient(135deg, ${severityColor}, ${incident.bgColor});
          width: 40px;
          height: 40px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 4px 12px rgba(0,0,0,0.4);
          border: 3px solid white;
          font-size: 20px;
        ">
          ${incident.icon}
        </div>
      `,
      iconSize: [40, 40],
      iconAnchor: [20, 40],
      popupAnchor: [0, -40]
    })
  }

  return (
    <MapContainer
      center={defaultCenter}
      zoom={13}
      style={{ height: '100%', width: '100%' }}
      zoomControl={true}
      scrollWheelZoom={true}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      
      {/* Marcadores de reportes */}
      {reports.map((report) => {
        // Parsear ubicación (en producción esto vendría como coordenadas)
        // Por ahora usamos coordenadas aleatorias cercanas al centro
        const lat = defaultCenter[0] + (Math.random() - 0.5) * 0.1
        const lng = defaultCenter[1] + (Math.random() - 0.5) * 0.1
        
        return (
          <Marker
            key={report.id}
            position={[lat, lng]}
            icon={createCustomIcon(report.tipo_incidente, report.severidad)}
          >
            <Popup className="custom-popup">
              <div className="min-w-[200px] text-dark-100">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-2xl">
                    {getIncidentIcon(report.tipo_incidente).icon}
                  </span>
                  <div>
                    <h3 className="font-bold text-white">{report.tipo_incidente}</h3>
                    <span 
                      className="text-xs px-2 py-1 rounded-full"
                      style={{
                        backgroundColor: `${getSeverityColor(report.severidad)}40`,
                        color: getSeverityColor(report.severidad)
                      }}
                    >
                      {report.severidad.toUpperCase()}
                    </span>
                  </div>
                </div>
                <p className="text-sm text-dark-300 mb-2">{report.descripcion}</p>
                <div className="flex items-center gap-1 text-xs text-dark-400">
                  <MapPin className="w-3 h-3" />
                  <span>{report.ubicacion}</span>
                </div>
                <div className="text-xs text-dark-400 mt-2">
                  {new Date(report.created_at).toLocaleString('es-ES')}
                </div>
              </div>
            </Popup>
          </Marker>
        )
      })}
      
      <MapController center={defaultCenter} />
    </MapContainer>
  )
}
