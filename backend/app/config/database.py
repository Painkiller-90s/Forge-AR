from pymongo import AsyncMongoClient

from app.config.settings import settings


client = AsyncMongoClient(
    settings.mongodb_url
)

database = client[
    settings.mongodb_db_name
]



async def connect_to_mongo():
    # Verificar la conexión con MongoDB.
    await client.admin.command("ping")

    # Índice único para los correos de usuarios.
    await database.users.create_index(
        "email",
        unique=True,
    )

    # HU007: impedir métricas duplicadas por postulación,
    # sello discográfico y plataforma externa.
    await database.metricas_externas.create_index(
        [
            ("postulacion_id", 1),
            ("sello_id", 1),
            ("plataforma", 1),
        ],
        unique=True,
        name="uq_metricas_postulacion_sello_plataforma",
    )

    print("MongoDB conectado correctamente")
    print("Índices de base de datos verificados")



async def close_mongo_connection():
    await client.close()

    print("Conexión con MongoDB cerrada")