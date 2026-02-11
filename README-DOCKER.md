# UrbanDrive - Guía de Docker Compose

## 📋 Descripción

Este `docker-compose.yml` orquesta todos los servicios de UrbanDrive en una arquitectura de microservicios completa.

## 🏗️ Arquitectura

### Servicios Incluidos

1. **API Gateway** (Nginx) - Puerto 80
2. **Microservicios**:
   - `auth-service` - Puerto 8001
   - `traffic-service` - Puerto 8002
   - `ai-service` - Puerto 8003
   - `gamification-service` - Puerto 8004
   - `notification-service` - Puerto 8005

3. **Infraestructura**:
   - **PostgreSQL 16** - Puerto 5432 (con bases de datos independientes)
   - **Redis 7** - Puerto 6379 (para gamificación y cache)
   - **RabbitMQ 3** - Puertos 5672 (AMQP) y 15672 (Management UI)

## 🚀 Inicio Rápido

### 1. Configurar Variables de Entorno

```bash
# Copiar el archivo de ejemplo
cp env.example .env

# Editar .env con tus valores (especialmente contraseñas y JWT_SECRET)
nano .env
```

### 2. Construir e Iniciar Servicios

```bash
# Construir todas las imágenes
docker compose build

# Iniciar todos los servicios
docker compose up -d

# Ver logs
docker compose logs -f

# Ver estado de los servicios
docker compose ps
```

### 3. Verificar Salud de los Servicios

```bash
# Verificar healthchecks
docker compose ps

# Probar endpoints
curl http://localhost/health
curl http://localhost:8001/health  # auth-service
curl http://localhost:8002/health  # traffic-service
```

## 🗄️ Bases de Datos

### PostgreSQL - Bases de Datos Independientes

Cada microservicio tiene su propia base de datos:

- `auth_db` - Servicio de autenticación
- `traffic_db` - Servicio de tráfico
- `ai_db` - Servicio de IA
- `gamification_db` - Servicio de gamificación
- `notification_db` - Servicio de notificaciones

Las bases de datos se crean automáticamente al iniciar PostgreSQL usando el script `scripts/init-multiple-databases.sh`.

### Redis - Bases de Datos por Servicio

Redis usa diferentes bases de datos (0-15) para cada servicio:

- DB 0: Gamificación (leaderboard, XP, badges)
- DB 1: Auth (sessions, tokens)
- DB 2: Traffic (cache)
- DB 3: AI (estadísticas de anomalías)
- DB 4: Notifications (cola de notificaciones)

## 🔐 Seguridad

### Variables de Entorno Críticas

1. **JWT_SECRET**: Debe ser una cadena segura de al menos 32 caracteres
2. **DB_PASS**: Contraseña fuerte para PostgreSQL
3. **RABBITMQ_PASS**: Contraseña para RabbitMQ
4. **REDIS_PASSWORD**: (Opcional) Contraseña para Redis

### Recomendaciones

- **NUNCA** subas el archivo `.env` al repositorio
- Usa secretos diferentes en producción
- Considera usar un gestor de secretos (AWS Secrets Manager, HashiCorp Vault)
- Rota las contraseñas regularmente

## 📊 Monitoreo

### RabbitMQ Management UI

Accede a la interfaz de gestión de RabbitMQ en:
```
http://localhost:15672
Usuario: urban_user (o el valor de RABBITMQ_USER)
Contraseña: urban_rabbitmq_pass_2024 (o el valor de RABBITMQ_PASS)
```

### Ver Logs

```bash
# Todos los servicios
docker compose logs -f

# Servicio específico
docker compose logs -f traffic-service

# Últimas 100 líneas
docker compose logs --tail=100 traffic-service
```

## 🔧 Comandos Útiles

### Gestión de Servicios

```bash
# Detener todos los servicios
docker compose down

# Detener y eliminar volúmenes (⚠️ elimina datos)
docker compose down -v

# Reiniciar un servicio específico
docker compose restart traffic-service

# Reconstruir un servicio
docker compose up -d --build traffic-service

# Ver uso de recursos
docker stats
```

### Base de Datos

```bash
# Conectar a PostgreSQL
docker exec -it urban_postgres psql -U urban_user -d traffic_db

# Backup de una base de datos
docker exec urban_postgres pg_dump -U urban_user traffic_db > backup.sql

# Restaurar backup
docker exec -i urban_postgres psql -U urban_user traffic_db < backup.sql
```

### Redis

```bash
# Conectar a Redis CLI
docker exec -it urban_redis redis-cli

# Ver todas las claves (gamificación)
docker exec urban_redis redis-cli -n 0 KEYS "*"

# Ver leaderboard
docker exec urban_redis redis-cli -n 0 ZREVRANGE leaderboard:xp 0 10 WITHSCORES
```

## 🌐 Red Interna

Todos los servicios están en la red `urban_network` (subnet: 172.28.0.0/16).

Los servicios pueden comunicarse entre sí usando los nombres de contenedor:
- `http://auth-service:8000`
- `http://traffic-service:8000`
- `amqp://rabbitmq:5672`
- `postgres:5432`
- `redis:6379`

## 📦 Volúmenes Persistentes

Los siguientes volúmenes se crean automáticamente:

- `postgres_data` - Datos de PostgreSQL
- `redis_data` - Datos de Redis (AOF)
- `rabbitmq_data` - Datos de RabbitMQ

Para eliminar todos los datos:
```bash
docker compose down -v
```

## 🐛 Troubleshooting

### Servicio no inicia

1. Verificar logs: `docker compose logs <service-name>`
2. Verificar healthcheck: `docker compose ps`
3. Verificar variables de entorno: `docker compose config`

### Error de conexión a base de datos

1. Verificar que PostgreSQL esté saludable: `docker compose ps postgres`
2. Verificar variables DB_USER y DB_PASS en .env
3. Verificar que las bases de datos se crearon: `docker exec urban_postgres psql -U urban_user -l`

### Error de conexión a RabbitMQ

1. Verificar que RabbitMQ esté saludable: `docker compose ps rabbitmq`
2. Verificar credenciales en .env
3. Acceder a Management UI para verificar conexiones

## 📝 Notas Adicionales

- Los healthchecks aseguran que los servicios estén listos antes de iniciar dependencias
- Los servicios se reinician automáticamente si fallan (`restart: unless-stopped`)
- Las imágenes Alpine se usan para reducir el tamaño de los contenedores
- El script de inicialización de PostgreSQL requiere permisos de ejecución

## 🔄 Actualización

Para actualizar los servicios:

```bash
# Detener servicios
docker compose down

# Actualizar código
git pull

# Reconstruir e iniciar
docker compose up -d --build
```
