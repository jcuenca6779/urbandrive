# UrbanDrive - Guía de Configuración Rápida

## 🚀 Inicio Rápido

### Linux/macOS

```bash
# Dar permisos de ejecución al script
chmod +x setup.sh

# Ejecutar el script
./setup.sh
```

### Windows (PowerShell)

```powershell
# Ejecutar el script de PowerShell
.\setup.ps1
```

## 📋 ¿Qué hace el script?

El script `setup.sh` (o `setup.ps1` en Windows) automatiza completamente la configuración del proyecto:

1. ✅ **Verifica Docker**: Comprueba que Docker esté instalado y corriendo
2. ✅ **Crea red Docker**: Crea la red `urban_network` si no existe
3. ✅ **Configura .env**: Crea el archivo `.env` desde `env.example` si no existe
4. ✅ **Construye servicios**: Ejecuta `docker-compose up --build -d`
5. ✅ **Muestra información**: Lista todos los puertos y endpoints disponibles

## 🔧 Requisitos Previos

- Docker Desktop instalado y corriendo
- Docker Compose (incluido en Docker Desktop)
- Git (opcional, para clonar el repositorio)

## 📝 Pasos Manuales (si prefieres no usar el script)

### 1. Crear red Docker

```bash
docker network create urban_network --driver bridge --subnet 172.28.0.0/16
```

### 2. Configurar variables de entorno

```bash
# Linux/macOS
cp env.example .env

# Windows
copy env.example .env
```

Edita el archivo `.env` y actualiza las credenciales según sea necesario.

### 3. Dar permisos al script de PostgreSQL

```bash
chmod +x scripts/init-multiple-databases.sh
```

### 4. Iniciar servicios

```bash
docker compose up --build -d
```

## 🌐 Puertos por Defecto

Después de ejecutar el script, los servicios estarán disponibles en:

| Servicio | Puerto | URL |
|----------|--------|-----|
| API Gateway | 80 | http://localhost |
| Auth Service | 8001 | http://localhost:8001 |
| Traffic Service | 8002 | http://localhost:8002 |
| AI Service | 8003 | http://localhost:8003 |
| Gamification Service | 8004 | http://localhost:8004 |
| Notification Service | 8005 | http://localhost:8005 |
| PostgreSQL | 5432 | localhost:5432 |
| Redis | 6379 | localhost:6379 |
| RabbitMQ | 5672 | localhost:5672 |
| RabbitMQ Management | 15672 | http://localhost:15672 |

## 🔍 Verificar que todo funciona

```bash
# Ver estado de los servicios
docker compose ps

# Ver logs
docker compose logs -f

# Probar endpoints
curl http://localhost/health
curl http://localhost:8001/health  # Auth Service
curl http://localhost:8002/health  # Traffic Service
```

## 🛠️ Comandos Útiles

```bash
# Ver logs de un servicio específico
docker compose logs -f auth-service

# Reiniciar un servicio
docker compose restart auth-service

# Detener todos los servicios
docker compose down

# Detener y eliminar volúmenes (⚠️ elimina datos)
docker compose down -v

# Reconstruir un servicio específico
docker compose up -d --build auth-service
```

## ⚠️ Solución de Problemas

### Error: "Docker no está corriendo"
- Asegúrate de que Docker Desktop esté iniciado
- En Linux, verifica que el servicio Docker esté activo: `sudo systemctl status docker`

### Error: "Puerto ya en uso"
- Verifica qué proceso está usando el puerto
- Cambia el puerto en el archivo `.env`

### Error: "No se puede conectar a la base de datos"
- Espera unos segundos a que PostgreSQL termine de inicializarse
- Verifica las credenciales en `.env`
- Revisa los logs: `docker compose logs postgres`

### Error: "Permiso denegado" en scripts
```bash
chmod +x scripts/init-multiple-databases.sh
```

## 📚 Documentación Adicional

- [README-DOCKER.md](README-DOCKER.md) - Documentación completa de Docker Compose
- [env.example](env.example) - Variables de entorno disponibles

## 🎉 ¡Listo!

Una vez que el script termine exitosamente, tu proyecto UrbanDrive estará corriendo y listo para usar.
