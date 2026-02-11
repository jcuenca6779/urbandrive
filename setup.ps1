# ============================================
# UrbanDrive - Script de Configuración (PowerShell)
# ============================================
# Este script automatiza el levantamiento del proyecto UrbanDrive en Windows

$ErrorActionPreference = "Stop"

# Colores para output
function Write-Info {
    Write-Host "[INFO] $args" -ForegroundColor Cyan
}

function Write-Success {
    Write-Host "[SUCCESS] $args" -ForegroundColor Green
}

function Write-Warning {
    Write-Host "[WARNING] $args" -ForegroundColor Yellow
}

function Write-Error {
    Write-Host "[ERROR] $args" -ForegroundColor Red
}

# Banner de inicio
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  UrbanDrive - Setup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que Docker esté instalado y corriendo
Write-Info "Verificando Docker..."
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker no está instalado. Por favor instala Docker Desktop primero."
    exit 1
}

try {
    docker info | Out-Null
    Write-Success "Docker está instalado y corriendo"
} catch {
    Write-Error "Docker no está corriendo. Por favor inicia Docker Desktop."
    exit 1
}

# Verificar que Docker Compose esté disponible
Write-Info "Verificando Docker Compose..."
if (docker compose version 2>$null) {
    $DOCKER_COMPOSE_CMD = "docker compose"
    Write-Success "Usando Docker Compose v2"
} elseif (Get-Command docker-compose -ErrorAction SilentlyContinue) {
    $DOCKER_COMPOSE_CMD = "docker-compose"
    Write-Success "Usando Docker Compose v1"
} else {
    Write-Error "Docker Compose no está instalado."
    exit 1
}

# Paso 1: Crear red de Docker si no existe
Write-Info "Verificando red Docker 'urban_network'..."
$networkExists = docker network inspect urban_network 2>$null
if ($networkExists) {
    Write-Warning "La red 'urban_network' ya existe"
} else {
    Write-Info "Creando red Docker 'urban_network'..."
    docker network create urban_network --driver bridge --subnet 172.28.0.0/16
    Write-Success "Red 'urban_network' creada exitosamente"
}

# Paso 2: Crear archivo .env si no existe
Write-Info "Verificando archivo .env..."
if (Test-Path .env) {
    Write-Warning "El archivo .env ya existe"
    $response = Read-Host "¿Deseas sobrescribirlo? (s/N)"
    if ($response -ne "s" -and $response -ne "S") {
        Write-Info "Manteniendo el archivo .env existente"
    } else {
        Write-Info "Copiando env.example a .env..."
        Copy-Item env.example .env
        Write-Success "Archivo .env creado desde env.example"
        Write-Warning "IMPORTANTE: Revisa y actualiza las credenciales en .env antes de continuar"
    }
} else {
    if (Test-Path env.example) {
        Write-Info "Creando archivo .env desde env.example..."
        Copy-Item env.example .env
        Write-Success "Archivo .env creado desde env.example"
        Write-Warning "IMPORTANTE: Revisa y actualiza las credenciales en .env antes de continuar"
    } else {
        Write-Error "No se encontró el archivo env.example"
        exit 1
    }
}

# Paso 3: Verificar que el script de inicialización de PostgreSQL tenga permisos
if (Test-Path scripts\init-multiple-databases.sh) {
    Write-Info "Script de inicialización de PostgreSQL encontrado"
}

# Paso 4: Construir e iniciar los servicios
Write-Info "Construyendo e iniciando los servicios con Docker Compose..."
Write-Host ""

# Ejecutar docker-compose up --build -d
try {
    Invoke-Expression "$DOCKER_COMPOSE_CMD up --build -d"
    Write-Success "Servicios iniciados exitosamente"
} catch {
    Write-Error "Error al iniciar los servicios"
    exit 1
}

Write-Host ""
Write-Info "Esperando a que los servicios estén listos..."
Start-Sleep -Seconds 5

# Paso 5: Obtener información de los puertos
Write-Success "=========================================="
Write-Success "  UrbanDrive está corriendo!"
Write-Success "=========================================="
Write-Host ""

Write-Info "Servicios disponibles:"
Write-Host ""

# Leer puertos del archivo .env
$envContent = Get-Content .env -Raw

function Get-Port {
    param($Key, $Default)
    $match = [regex]::Match($envContent, "$Key=([^\r\n]+)")
    if ($match.Success) {
        return $match.Groups[1].Value.Trim('"')
    }
    return $Default
}

$GATEWAY_PORT = Get-Port "GATEWAY_PORT" "80"
$AUTH_PORT = Get-Port "AUTH_SERVICE_PORT" "8001"
$TRAFFIC_PORT = Get-Port "TRAFFIC_SERVICE_PORT" "8002"
$AI_PORT = Get-Port "AI_SERVICE_PORT" "8003"
$GAMIFICATION_PORT = Get-Port "GAMIFICATION_SERVICE_PORT" "8004"
$NOTIFICATION_PORT = Get-Port "NOTIFICATION_SERVICE_PORT" "8005"
$POSTGRES_PORT = Get-Port "POSTGRES_PORT" "5432"
$REDIS_PORT = Get-Port "REDIS_PORT" "6379"
$RABBITMQ_PORT = Get-Port "RABBITMQ_PORT" "5672"
$RABBITMQ_MGMT_PORT = Get-Port "RABBITMQ_MANAGEMENT_PORT" "15672"

Write-Host "  ✓ API Gateway:        http://localhost:$GATEWAY_PORT" -ForegroundColor Green
Write-Host "  ✓ Auth Service:       http://localhost:$AUTH_PORT" -ForegroundColor Green
Write-Host "  ✓ Traffic Service:     http://localhost:$TRAFFIC_PORT" -ForegroundColor Green
Write-Host "  ✓ AI Service:          http://localhost:$AI_PORT" -ForegroundColor Green
Write-Host "  ✓ Gamification Service: http://localhost:$GAMIFICATION_PORT" -ForegroundColor Green
Write-Host "  ✓ Notification Service: http://localhost:$NOTIFICATION_PORT" -ForegroundColor Green
Write-Host "  ✓ PostgreSQL:          localhost:$POSTGRES_PORT" -ForegroundColor Green
Write-Host "  ✓ Redis:               localhost:$REDIS_PORT" -ForegroundColor Green
Write-Host "  ✓ RabbitMQ:            localhost:$RABBITMQ_PORT" -ForegroundColor Green
Write-Host "  ✓ RabbitMQ Management:  http://localhost:$RABBITMQ_MGMT_PORT" -ForegroundColor Green

Write-Host ""
Write-Info "Endpoints del API Gateway:"
Write-Host "  → http://localhost:$GATEWAY_PORT/api/auth/*" -ForegroundColor Cyan
Write-Host "  → http://localhost:$GATEWAY_PORT/api/traffic/*" -ForegroundColor Cyan
Write-Host "  → http://localhost:$GATEWAY_PORT/api/gamification/*" -ForegroundColor Cyan
Write-Host "  → http://localhost:$GATEWAY_PORT/api/ai/*" -ForegroundColor Cyan
Write-Host "  → http://localhost:$GATEWAY_PORT/api/notifications/*" -ForegroundColor Cyan

Write-Host ""
Write-Info "Comandos útiles:"
Write-Host "  Ver logs:              $DOCKER_COMPOSE_CMD logs -f"
Write-Host "  Ver estado:           $DOCKER_COMPOSE_CMD ps"
Write-Host "  Detener servicios:    $DOCKER_COMPOSE_CMD down"
Write-Host "  Reiniciar servicio:   $DOCKER_COMPOSE_CMD restart <service-name>"

Write-Host ""
Write-Success "¡Configuración completada exitosamente!"
Write-Host ""
