# Qué hacer ANTES de ejecutar UrbanDrive

## Resumen: solo 1 archivo obligatorio

**No tienes que crear bases de datos a mano.**  
**No tienes que modificar código.**  
Solo necesitas **un archivo de configuración** (`.env`) y, en Linux/macOS, permisos en un script.

---

## 1. Archivo que SÍ tienes que tener: `.env`

### Crear el archivo

- **Windows (PowerShell):**
  ```powershell
  Copy-Item env.example .env
  ```
- **Linux o macOS:**
  ```bash
  cp env.example .env
  ```

El archivo debe quedar en la **raíz del proyecto** (misma carpeta que `docker-compose.yml`).

### Revisar (recomendado) antes de la primera ejecución

Abre `.env` y comprueba al menos:

| Variable      | Qué hacer |
|---------------|-----------|
| `JWT_SECRET`  | Debe tener **al menos 32 caracteres**. Si sigue siendo el de ejemplo, cámbialo por una frase o clave larga. |
| `DB_PASS`     | Contraseña de PostgreSQL. Puedes dejarla o cambiarla. |
| `RABBITMQ_PASS` | Contraseña de RabbitMQ. Igual, opcional cambiarla. |

Ejemplo de `JWT_SECRET` válido:

```env
JWT_SECRET=mi_clave_super_secreta_urbandrive_2024_minimo_32_caracteres
```

**No hace falta tocar** el resto de variables para que funcione en local.

---

## 2. Bases de datos: no se crean a mano

- **PostgreSQL**: al levantar el contenedor por **primera vez**, se ejecuta el script `scripts/init-multiple-databases.sh` y se crean solas estas bases:
  - `auth_db`
  - `traffic_db`
  - `ai_db`
  - `gamification_db`
  - `notification_db`
- **Tablas**: cada microservicio crea sus tablas al arrancar (con SQLAlchemy). No tienes que ejecutar ningún SQL ni script extra.
- **Redis**: no hay que crear bases ni índices; los servicios usan Redis directamente.
- **RabbitMQ**: los servicios declaran el exchange y las colas al conectarse. Tampoco hay que crear nada a mano.

Conclusión: **no creas bases de datos ni tablas manualmente.**

---

## 3. Script de PostgreSQL (solo Linux/macOS)

El script que crea las bases está en:

`scripts/init-multiple-databases.sh`

En **Linux o macOS** debe ser ejecutable; si no, PostgreSQL puede no ejecutarlo al iniciar por primera vez:

```bash
chmod +x scripts/init-multiple-databases.sh
```

En **Windows** no hace falta ejecutar `chmod` (el script se ejecuta dentro del contenedor Linux).

---

## 4. Qué NO hace falta modificar

- No editar `docker-compose.yml` para que funcione en local.
- No tocar código de los servicios (auth, traffic, ai, gamification, notification).
- No instalar PostgreSQL, Redis ni RabbitMQ en tu PC; todo va en contenedores.
- No crear a mano bases de datos ni tablas.

---

## 5. Orden recomendado antes de la primera vez

1. Tener **Docker** (y Docker Compose) instalado y en marcha.
2. En la raíz del proyecto, crear **`.env`** a partir de `env.example`.
3. (Opcional) Ajustar en `.env`: `JWT_SECRET` (32+ caracteres), y si quieres, `DB_PASS` y `RABBITMQ_PASS`.
4. En **Linux/macOS**: ejecutar `chmod +x scripts/init-multiple-databases.sh`.
5. Levantar todo, por ejemplo:
   - Con script: `.\setup.ps1` (Windows) o `./setup.sh` (Linux/macOS).
   - O a mano: `docker compose up --build -d`.

Después de eso, las bases de datos y tablas se crean solas; tú solo necesitas el `.env` (y el `chmod` en Linux/macOS).
