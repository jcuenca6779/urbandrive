#!/bin/bash

# ============================================
# UrbanDrive - Script de Configuración
# ============================================
# Este script automatiza el levantamiento del proyecto UrbanDrive

set -e  # Salir si hay algún error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes con color
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner de inicio
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  UrbanDrive - Setup Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Verificar que Docker esté instalado y corriendo
print_info "Verificando Docker..."
if ! command -v docker &> /dev/null; then
    print_error "Docker no está instalado. Por favor instala Docker primero."
    exit 1
fi

if ! docker info &> /dev/null; then
    print_error "Docker no está corriendo. Por favor inicia Docker Desktop."
    exit 1
fi
print_success "Docker está instalado y corriendo"

# Verificar que Docker Compose esté disponible
print_info "Verificando Docker Compose..."
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose no está instalado."
    exit 1
fi

# Usar docker compose (v2) si está disponible, sino docker-compose (v1)
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
    print_success "Usando Docker Compose v2"
else
    DOCKER_COMPOSE_CMD="docker-compose"
    print_success "Usando Docker Compose v1"
fi

# Paso 1: Crear red de Docker si no existe
print_info "Verificando red Docker 'urban_network'..."
if docker network inspect urban_network &> /dev/null; then
    print_warning "La red 'urban_network' ya existe"
else
    print_info "Creando red Docker 'urban_network'..."
    docker network create urban_network --driver bridge --subnet 172.28.0.0/16
    print_success "Red 'urban_network' creada exitosamente"
fi

# Paso 2: Crear archivo .env si no existe
print_info "Verificando archivo .env..."
if [ -f .env ]; then
    print_warning "El archivo .env ya existe"
    read -p "¿Deseas sobrescribirlo? (s/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        print_info "Manteniendo el archivo .env existente"
    else
        print_info "Copiando env.example a .env..."
        cp env.example .env
        print_success "Archivo .env creado desde env.example"
        print_warning "IMPORTANTE: Revisa y actualiza las credenciales en .env antes de continuar"
    fi
else
    if [ -f env.example ]; then
        print_info "Creando archivo .env desde env.example..."
        cp env.example .env
        print_success "Archivo .env creado desde env.example"
        print_warning "IMPORTANTE: Revisa y actualiza las credenciales en .env antes de continuar"
    else
        print_error "No se encontró el archivo env.example"
        exit 1
    fi
fi

# Paso 3: Verificar que el script de inicialización de PostgreSQL tenga permisos
if [ -f scripts/init-multiple-databases.sh ]; then
    print_info "Configurando permisos del script de inicialización de PostgreSQL..."
    chmod +x scripts/init-multiple-databases.sh
    print_success "Permisos configurados"
fi

# Paso 4: Construir e iniciar los servicios
print_info "Construyendo e iniciando los servicios con Docker Compose..."
echo ""

# Ejecutar docker-compose up --build -d
if $DOCKER_COMPOSE_CMD up --build -d; then
    print_success "Servicios iniciados exitosamente"
else
    print_error "Error al iniciar los servicios"
    exit 1
fi

echo ""
print_info "Esperando a que los servicios estén listos..."
sleep 5

# Paso 5: Verificar estado de los servicios
print_info "Verificando estado de los servicios..."
echo ""

# Obtener información de los puertos desde docker-compose
print_success "=========================================="
print_success "  UrbanDrive está corriendo!"
print_success "=========================================="
echo ""

# Obtener puertos de los servicios
print_info "Servicios disponibles:"
echo ""

# Gateway
GATEWAY_PORT=$(grep -E "^\s*GATEWAY_PORT=" .env 2>/dev/null | cut -d '=' -f2 | tr -d '"' || echo "80")
echo -e "  ${GREEN}✓${NC} API Gateway:        http://localhost:${GATEWAY_PORT}"

# Auth Service
AUTH_PORT=$(grep -E "^\s*AUTH_SERVICE_PORT=" .env 2>/dev/null | cut -d '=' -f2 | tr -d '"' || echo "8001")
echo -e "  ${GREEN}✓${NC} Auth Service:       http://localhost:${AUTH_PORT}"

# Traffic Service
TRAFFIC_PORT=$(grep -E "^\s*TRAFFIC_SERVICE_PORT=" .env 2>/dev/null | cut -d '=' -f2 | tr -d '"' || echo "8002")
echo -e "  ${GREEN}✓${NC} Traffic Service:     http://localhost:${TRAFFIC_PORT}"

# AI Service
AI_PORT=$(grep -E "^\s*AI_SERVICE_PORT=" .env 2>/dev/null | cut -d '=' -f2 | tr -d '"' || echo "8003")
echo -e "  ${GREEN}✓${NC} AI Service:          http://localhost:${AI_PORT}"

# Gamification Service
GAMIFICATION_PORT=$(grep -E "^\s*GAMIFICATION_SERVICE_PORT=" .env 2>/dev/null | cut -d '=' -f2 | tr -d '"' || echo "8004")
echo -e "  ${GREEN}✓${NC} Gamification Service: http://localhost:${GAMIFICATION_PORT}"

# Notification Service
NOTIFICATION_PORT=$(grep -E "^\s*NOTIFICATION_SERVICE_PORT=" .env 2>/dev/null | cut -d '=' -f2 | tr -d '"' || echo "8005")
echo -e "  ${GREEN}✓${NC} Notification Service: http://localhost:${NOTIFICATION_PORT}"

# PostgreSQL
POSTGRES_PORT=$(grep -E "^\s*POSTGRES_PORT=" .env 2>/dev/null | cut -d '=' -f2 | tr -d '"' || echo "5432")
echo -e "  ${GREEN}✓${NC} PostgreSQL:          localhost:${POSTGRES_PORT}"

# Redis
REDIS_PORT=$(grep -E "^\s*REDIS_PORT=" .env 2>/dev/null | cut -d '=' -f2 | tr -d '"' || echo "6379")
echo -e "  ${GREEN}✓${NC} Redis:               localhost:${REDIS_PORT}"

# RabbitMQ
RABBITMQ_PORT=$(grep -E "^\s*RABBITMQ_PORT=" .env 2>/dev/null | cut -d '=' -f2 | tr -d '"' || echo "5672")
RABBITMQ_MGMT_PORT=$(grep -E "^\s*RABBITMQ_MANAGEMENT_PORT=" .env 2>/dev/null | cut -d '=' -f2 | tr -d '"' || echo "15672")
echo -e "  ${GREEN}✓${NC} RabbitMQ:            localhost:${RABBITMQ_PORT}"
echo -e "  ${GREEN}✓${NC} RabbitMQ Management:  http://localhost:${RABBITMQ_MGMT_PORT}"

echo ""
print_info "Endpoints del API Gateway:"
echo -e "  ${BLUE}→${NC} http://localhost:${GATEWAY_PORT}/api/auth/*"
echo -e "  ${BLUE}→${NC} http://localhost:${GATEWAY_PORT}/api/traffic/*"
echo -e "  ${BLUE}→${NC} http://localhost:${GATEWAY_PORT}/api/gamification/*"
echo -e "  ${BLUE}→${NC} http://localhost:${GATEWAY_PORT}/api/ai/*"
echo -e "  ${BLUE}→${NC} http://localhost:${GATEWAY_PORT}/api/notifications/*"

echo ""
print_info "Comandos útiles:"
echo "  Ver logs:              $DOCKER_COMPOSE_CMD logs -f"
echo "  Ver estado:           $DOCKER_COMPOSE_CMD ps"
echo "  Detener servicios:    $DOCKER_COMPOSE_CMD down"
echo "  Reiniciar servicio:   $DOCKER_COMPOSE_CMD restart <service-name>"

echo ""
print_success "¡Configuración completada exitosamente!"
echo ""
