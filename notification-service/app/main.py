from fastapi import FastAPI

app = FastAPI(title="UrbanDrive Notification Service")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "notification-service"}


@app.get("/info")
async def info():
    return {"service": "notification-service", "description": "Servicio de notificaciones de UrbanDrive"}

