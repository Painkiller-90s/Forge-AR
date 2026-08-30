from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routes.user_route import router as user_router
from app.routes.auth_route import router as auth_router

from app.config.database import (
    connect_to_mongo,
    close_mongo_connection
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()

    yield

    await close_mongo_connection()


app = FastAPI(
    title="Forge A&R API",
    description="Backend de la plataforma Forge A&R",
    version="1.0.0",
    lifespan=lifespan
)
app.include_router(user_router)
app.include_router(auth_router)


@app.get("/")
async def root():
    return {
        "message": "Forge A&R API funcionando"
    }