
import os

from apify_client import ApifyClientAsync
from dotenv import load_dotenv


load_dotenv()

ACTOR_ID = "apify/instagram-profile-scraper"


async def consultar_perfil_instagram(usuario: str) -> dict:
    """
    Consulta un perfil público de Instagram mediante Apify.

    Recibe un nombre de usuario previamente validado.
    Devuelve los datos obtenidos sin almacenarlos.
    """

    token = os.getenv("APIFY_API_TOKEN")

    if not token:
        raise RuntimeError(
            "El token de Apify no está configurado."
        )

    cliente = ApifyClientAsync(token=token)

    # Ejecutar el actor con un único usuario.
    ejecucion = await cliente.actor(ACTOR_ID).call(
        run_input={
            "usernames": [usuario]
        }
    )

    if ejecucion is None or not ejecucion.default_dataset_id:
        raise RuntimeError(
            "Apify no devolvió una ejecución válida."
        )

    # Recuperar únicamente el resultado del perfil.
    respuesta = await cliente.dataset(
        ejecucion.default_dataset_id
    ).list_items(limit=1)

    if not respuesta.items:
        raise ValueError(
            "No se encontraron datos para el perfil."
        )

    perfil = respuesta.items[0]

    if perfil.get("username", "").lower() != usuario.lower():
        raise ValueError(
            "El perfil obtenido no coincide con el solicitado."
        )

    return perfil
