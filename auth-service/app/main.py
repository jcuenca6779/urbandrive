from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.database import get_db, init_db
from app.models import Usuario, RolEnum
from app.schemas import UsuarioCreate, UsuarioResponse, UsuarioLogin, TokenResponse
from app.security import verify_password, get_password_hash, create_access_token
from app.dependencies import get_current_active_user

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="UrbanDrive Auth Service",
    description="Servicio de autenticación y autorización para UrbanDrive",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """Inicializar base de datos al arrancar la aplicación"""
    logger.info("Inicializando base de datos...")
    init_db()
    logger.info("Base de datos inicializada correctamente")


@app.get("/health")
async def health_check():
    """Endpoint de salud del servicio"""
    return {"status": "ok", "service": "auth-service"}


@app.get("/info")
async def info():
    """Información del servicio"""
    return {
        "service": "auth-service",
        "description": "Servicio de autenticación de UrbanDrive",
        "endpoints": {
            "POST /register": "Registro de nuevos usuarios",
            "POST /login": "Inicio de sesión y obtención de token",
            "GET /me": "Información del usuario autenticado"
        }
    }


@app.post(
    "/register",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registro de usuario",
    description="Registra un nuevo usuario en el sistema"
)
async def register(
    user_data: UsuarioCreate,
    db: Session = Depends(get_db)
):
    """
    Registra un nuevo usuario en el sistema.
    
    - **nombre**: Nombre completo del usuario
    - **email**: Email del usuario (debe ser único)
    - **password**: Contraseña (mínimo 8 caracteres)
    - **rol**: Rol del usuario (conductor, colaborador, admin)
    """
    # Verificar si el email ya existe
    existing_user = db.query(Usuario).filter(Usuario.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )
    
    # Crear nuevo usuario
    hashed_password = get_password_hash(user_data.password)
    
    db_user = Usuario(
        nombre=user_data.nombre,
        email=user_data.email,
        password_hash=hashed_password,
        rol=user_data.rol
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    logger.info(f"Usuario registrado: {db_user.email} (ID: {db_user.id})")
    
    return db_user


@app.post(
    "/login",
    response_model=TokenResponse,
    summary="Inicio de sesión",
    description="Valida credenciales y retorna un token JWT"
)
async def login(
    credentials: UsuarioLogin,
    db: Session = Depends(get_db)
):
    """
    Inicia sesión y obtiene un token JWT.
    
    - **email**: Email del usuario
    - **password**: Contraseña del usuario
    
    Retorna un token JWT que debe ser incluido en el header Authorization
    de las peticiones protegidas.
    """
    # Buscar usuario por email
    user = db.query(Usuario).filter(Usuario.email == credentials.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar contraseña
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar que el usuario esté activo
    if user.is_active != "true":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    
    # Crear token JWT
    access_token = create_access_token(data={"sub": user.id, "email": user.email, "rol": user.rol.value})
    
    logger.info(f"Usuario autenticado: {user.email} (ID: {user.id})")
    
    # Importar JWT_EXPIRATION desde security
    from app.security import JWT_EXPIRATION
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=JWT_EXPIRATION,
        user=UsuarioResponse.model_validate(user)
    )


@app.get(
    "/me",
    response_model=UsuarioResponse,
    summary="Usuario actual",
    description="Obtiene la información del usuario autenticado usando el token JWT"
)
async def get_current_user_info(
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtiene la información del usuario autenticado.
    
    Requiere un token JWT válido en el header Authorization.
    
    Retorna:
    - **id**: ID del usuario
    - **nombre**: Nombre del usuario
    - **email**: Email del usuario
    - **rol**: Rol del usuario
    - **is_active**: Estado del usuario
    - **created_at**: Fecha de creación
    - **updated_at**: Fecha de última actualización
    """
    return UsuarioResponse.model_validate(current_user)

