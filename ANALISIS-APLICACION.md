# 📊 Análisis Completo de UrbanDrive - Guía de Puesta en Marcha

## 🎯 Estado Actual de la Aplicación

### ✅ Componentes Implementados

#### 1. **Microservicios Backend** (Python + FastAPI)
- ✅ **auth-service**: Autenticación con JWT, registro, login, roles
- ✅ **traffic-service**: Reportes de incidentes, validación social, RabbitMQ producer
- ✅ **ai-service**: Análisis de sentimiento, detección de falsos positivos, re-entrenamiento
- ✅ **gamification-service**: Sistema de XP, badges, leaderboard, RabbitMQ consumer
- ✅ **notification-service**: Estructura básica (pendiente implementación completa)

#### 2. **Infraestructura**
- ✅ **PostgreSQL**: Base de datos con múltiples DBs por servicio
- ✅ **Redis**: Cache y gamificación
- ✅ **RabbitMQ**: Mensajería asíncrona
- ✅ **Nginx Gateway**: API Gateway con routing y CORS

#### 3. **Frontend** (React + Tailwind CSS)
- ✅ Interfaz de login
- ✅ Mapa interactivo con react-leaflet
- ✅ Panel de gamificación
- ✅ Modal de reportes
- ✅ Context de autenticación
- ✅ Integración con API Gateway

#### 4. **Automatización**
- ✅ Scripts de setup (setup.sh y setup.ps1)
- ✅ Docker Compose completo
- ✅ Healthchecks configurados

---

## 🔍 Verificaciones Necesarias Antes de Iniciar

### 1. **Requisitos del Sistema**

```bash
# Verificar Docker
docker --version
docker compose version

# Verificar que Docker Desktop esté corriendo (Windows)
# Verificar que Docker daemon esté corriendo (Linux)
```

### 2. **Archivos de Configuración**

- ✅ `.env` existe (ya verificado)
- ⚠️ Verificar que `.env` tenga valores correctos (especialmente `JWT_SECRET`)

### 3. **Puertos Disponibles**

Verificar que estos puertos estén libres:
- `80` - Gateway
- `8001` - Auth Service
- `8002` - Traffic Service
- `8003` - AI Service
- `8004` - Gamification Service
- `8005` - Notification Service
- `5432` - PostgreSQL
- `6379` - Redis
- `5672` - RabbitMQ AMQP
- `15672` - RabbitMQ Management

---

## 🚀 Pasos para Poner en Funcionamiento

### **Paso 1: Verificar y Configurar Variables de Entorno**

```bash
# Si no tienes .env, copiarlo desde el ejemplo
cp env.example .env

# Editar .env y asegurarte de que JWT_SECRET tenga al menos 32 caracteres
# Ejemplo de JWT_SECRET seguro:
# JWT_SECRET=tu_clave_super_secreta_de_al_menos_32_caracteres_2024
```

**Variables críticas a verificar:**
- `JWT_SECRET` - Debe ser una cadena segura de mínimo 32 caracteres
- `DB_PASS` - Contraseña de PostgreSQL
- `RABBITMQ_PASS` - Contraseña de RabbitMQ
- `REDIS_PASSWORD` - Puede estar vacío (opcional)

### **Paso 2: Verificar Docker**

```bash
# Windows PowerShell
docker ps

# Linux/macOS
docker ps
```

Si Docker no está corriendo:
- **Windows**: Abrir Docker Desktop
- **Linux**: `sudo systemctl start docker`

### **Paso 3: Ejecutar Script de Setup**

#### **Windows (PowerShell):**
```powershell
.\setup.ps1
```

#### **Linux/macOS:**
```bash
chmod +x setup.sh
./setup.sh
```

#### **O manualmente:**

```bash
# 1. Crear red Docker
docker network create urban_network --driver bridge --subnet 172.28.0.0/16

# 2. Dar permisos al script de PostgreSQL (Linux/macOS)
chmod +x scripts/init-multiple-databases.sh

# 3. Construir e iniciar servicios
docker compose up --build -d

# 4. Ver logs
docker compose logs -f
```

### **Paso 4: Verificar que los Servicios Estén Corriendo**

```bash
# Ver estado de todos los servicios
docker compose ps

# Deberías ver algo como:
# NAME                      STATUS          PORTS
# urban_auth_service        Up (healthy)    0.0.0.0:8001->8000/tcp
# urban_traffic_service     Up (healthy)    0.0.0.0:8002->8000/tcp
# ...
```

### **Paso 5: Probar Endpoints de Salud**

```bash
# Gateway
curl http://localhost/health

# Servicios individuales
curl http://localhost:8001/health  # Auth
curl http://localhost:8002/health  # Traffic
curl http://localhost:8003/health  # AI
curl http://localhost:8004/health  # Gamification
```

### **Paso 6: Verificar Frontend**

```bash
# Si el frontend está en Docker, debería estar en:
# http://localhost (si está configurado en el gateway)
# O en el puerto configurado en docker-compose.yml
```

---

## 🔧 Configuración Detallada por Servicio

### **1. Auth Service**

**Endpoints principales:**
- `POST /api/auth/register` - Registro de usuarios
- `POST /api/auth/login` - Login y obtención de JWT
- `GET /api/auth/me` - Información del usuario actual

**Base de datos:** `auth_db`

**Verificación:**
```bash
# Probar registro
curl -X POST http://localhost/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Test User","email":"test@test.com","password":"test123","rol":"conductor"}'

# Probar login
curl -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test123"}'
```

### **2. Traffic Service**

**Endpoints principales:**
- `POST /api/traffic/reportar` - Reportar incidente
- `GET /api/traffic/reportes` - Listar incidentes activos
- `GET /api/traffic/reportes/cercanos` - Incidentes cercanos (GeoJSON)
- `POST /api/traffic/reportes/{id}/validar` - Validar reporte

**Base de datos:** `traffic_db`

**Dependencias:**
- ✅ AI Service (para clasificación de severidad)
- ✅ RabbitMQ (para publicar eventos)

**Verificación:**
```bash
# Probar reporte (necesita token JWT)
curl -X POST http://localhost/api/traffic/reportar \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "tipo": "choque",
    "descripcion": "Choque entre dos vehículos",
    "latitud": -12.0464,
    "longitud": -77.0428,
    "usuario_id": 1
  }'
```

### **3. AI Service**

**Endpoints principales:**
- `POST /api/ai/clasificar-severidad` - Clasificar severidad
- `POST /api/ai/clasificar-incidente` - Clasificar tipo de incidente
- `POST /api/ai/detectar-anomalia` - Detectar anomalías estadísticas
- `POST /api/ai/detectar-falso-positivo` - Detectar falsos positivos
- `POST /api/ai/train` - Re-entrenar modelos

**Base de datos:** `ai_db` (para datos de entrenamiento)

**Modelos ML:**
- Modelos guardados en `ai-service/models/`
- Se crean automáticamente al iniciar si no existen

**Verificación:**
```bash
# Probar clasificación de severidad
curl -X POST http://localhost/api/ai/clasificar-severidad \
  -H "Content-Type: application/json" \
  -d '{
    "tipo_incidente": "choque",
    "descripcion": "Choque grave con heridos"
  }'
```

### **4. Gamification Service**

**Endpoints principales:**
- `GET /api/gamification/profile/{user_id}` - Perfil del usuario
- `GET /api/gamification/leaderboard` - Tabla de posiciones

**Redis:** DB 0 (gamificación)

**RabbitMQ:** Escucha eventos `reporte_creado` y `reporte_validado`

**Verificación:**
```bash
# Ver perfil de usuario
curl http://localhost/api/gamification/profile/1

# Ver leaderboard
curl http://localhost/api/gamification/leaderboard
```

### **5. Gateway (Nginx)**

**Rutas configuradas:**
- `/api/auth/*` → `auth-service:8000`
- `/api/traffic/*` → `traffic-service:8000`
- `/api/ai/*` → `ai-service:8000`
- `/api/gamification/*` → `gamification-service:8000`
- `/api/notification/*` → `notification-service:8000`

**CORS:** Configurado para permitir todas las solicitudes (ajustar en producción)

---

## 🐛 Troubleshooting Común

### **Problema 1: Servicios no inician**

```bash
# Ver logs detallados
docker compose logs [nombre-servicio]

# Ejemplo:
docker compose logs traffic-service
docker compose logs postgres
```

**Soluciones comunes:**
- Verificar que los puertos no estén en uso
- Verificar que `.env` tenga todas las variables necesarias
- Verificar que Docker tenga suficientes recursos (RAM, CPU)

### **Problema 2: Error de conexión a base de datos**

```bash
# Verificar que PostgreSQL esté corriendo
docker compose ps postgres

# Ver logs de PostgreSQL
docker compose logs postgres

# Verificar que las bases de datos se crearon
docker exec -it urban_postgres psql -U urban_user -l
```

**Solución:**
- Verificar que `scripts/init-multiple-databases.sh` tenga permisos de ejecución
- Verificar variables `DB_USER` y `DB_PASS` en `.env`

### **Problema 3: RabbitMQ no conecta**

```bash
# Verificar RabbitMQ
docker compose ps rabbitmq

# Ver logs
docker compose logs rabbitmq

# Acceder a Management UI
# http://localhost:15672
# Usuario: urban_user (o RABBITMQ_USER)
# Contraseña: urban_rabbitmq_pass_2024 (o RABBITMQ_PASS)
```

### **Problema 4: Frontend no carga**

```bash
# Verificar que el frontend esté construido
cd frontend
npm install
npm run build

# Verificar logs del contenedor frontend
docker compose logs gateway
```

### **Problema 5: Modelos ML no se crean**

```bash
# Verificar que el directorio models existe
ls -la ai-service/models/

# Ver logs del ai-service
docker compose logs ai-service

# Los modelos se crean automáticamente al iniciar si no existen
```

---

## 📋 Checklist de Verificación

Antes de considerar la aplicación funcionando, verifica:

### **Infraestructura**
- [ ] Docker Desktop corriendo
- [ ] Todos los contenedores en estado "Up (healthy)"
- [ ] Red `urban_network` creada
- [ ] Archivo `.env` configurado correctamente

### **Bases de Datos**
- [ ] PostgreSQL corriendo y saludable
- [ ] Todas las bases de datos creadas (auth_db, traffic_db, ai_db, etc.)
- [ ] Redis corriendo
- [ ] RabbitMQ corriendo y accesible

### **Servicios Backend**
- [ ] Auth Service responde en `/health`
- [ ] Traffic Service responde en `/health`
- [ ] AI Service responde en `/health`
- [ ] Gamification Service responde en `/health`
- [ ] Gateway responde en `/health`

### **Funcionalidad**
- [ ] Puedo registrar un usuario
- [ ] Puedo hacer login y obtener JWT
- [ ] Puedo reportar un incidente
- [ ] Puedo ver incidentes cercanos
- [ ] Puedo validar un reporte
- [ ] El AI Service clasifica correctamente
- [ ] Los eventos se publican en RabbitMQ
- [ ] La gamificación otorga XP

### **Frontend**
- [ ] Frontend carga correctamente
- [ ] Puedo hacer login desde el frontend
- [ ] El mapa se muestra correctamente
- [ ] Puedo reportar incidentes desde el frontend
- [ ] El panel de gamificación muestra datos

---

## 🎯 Próximos Pasos Recomendados

### **1. Datos de Prueba**

Crear algunos datos de prueba para probar la funcionalidad:

```bash
# Registrar usuarios de prueba
# Reportar algunos incidentes
# Validar algunos reportes
# Verificar que la gamificación funcione
```

### **2. Monitoreo**

- Configurar logging centralizado
- Configurar métricas (Prometheus/Grafana)
- Configurar alertas

### **3. Seguridad**

- [ ] Cambiar todas las contraseñas por defecto
- [ ] Configurar HTTPS en producción
- [ ] Restringir CORS en producción
- [ ] Implementar rate limiting
- [ ] Configurar firewall

### **4. Optimización**

- [ ] Configurar índices en bases de datos
- [ ] Optimizar consultas geoespaciales
- [ ] Configurar cache en Redis
- [ ] Optimizar modelos ML

---

## 📞 Comandos Útiles de Referencia

```bash
# Ver todos los servicios
docker compose ps

# Ver logs en tiempo real
docker compose logs -f

# Reiniciar un servicio específico
docker compose restart traffic-service

# Reconstruir un servicio
docker compose up -d --build traffic-service

# Detener todos los servicios
docker compose down

# Detener y eliminar volúmenes (⚠️ elimina datos)
docker compose down -v

# Ver uso de recursos
docker stats

# Conectar a PostgreSQL
docker exec -it urban_postgres psql -U urban_user -d traffic_db

# Conectar a Redis
docker exec -it urban_redis redis-cli

# Ver colas de RabbitMQ
# Acceder a http://localhost:15672
```

---

## ✅ Resumen: Pasos Mínimos para Funcionar

1. **Verificar Docker está corriendo**
2. **Verificar/Crear archivo `.env`** (copiar de `env.example`)
3. **Ejecutar script de setup** (`setup.ps1` en Windows o `setup.sh` en Linux/macOS)
4. **Esperar a que todos los servicios estén "healthy"** (puede tomar 1-2 minutos)
5. **Probar endpoints de salud** (`curl http://localhost/health`)
6. **Acceder al frontend** (http://localhost si está configurado)

¡Listo! La aplicación debería estar funcionando. 🚀
