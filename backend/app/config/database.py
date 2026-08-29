from pymongo import AsyncMongoClient

from app.config.settings import settings


client = AsyncMongoClient(settings.mongodb_url)

database = client[settings.mongodb_db_name]


async def connect_to_mongo():
    await client.admin.command("ping")
    print("MongoDB conectado correctamente")


async def close_mongo_connection():
    await client.close()
    print("Conexión con MongoDB cerrada")