
import re
from urllib.parse import urlparse
from datetime import datetime, timezone
from app.services.apify_service import consultar_perfil_instagram


def extraer_usuario_instagram(url: str) -> str:
    """Extrae el usuario de una URL válida de perfil de Instagram."""

    if not isinstance(url, str) or not url.strip():
        raise ValueError("La URL de Instagram es obligatoria.")

    parsed = urlparse(url.strip())

    dominios_validos = {
        "instagram.com",
        "www.instagram.com",
        "m.instagram.com",
    }

    if parsed.scheme not in ("http", "https"):
        raise ValueError("El enlace de Instagram no es válido.")

    if parsed.hostname not in dominios_validos:
        raise ValueError("El enlace no pertenece a Instagram.")

    partes = [parte for parte in parsed.path.split("/") if parte]

    if len(partes) != 1:
        raise ValueError("Debes proporcionar un enlace de perfil.")

    usuario = partes[0]

    if not re.fullmatch(r"[A-Za-z0-9._]{1,30}", usuario):
        raise ValueError("El nombre de usuario no es válido.")

    if usuario.lower() in {
        "p", "reel", "reels", "stories", "explore", "direct"
    }:
        raise ValueError("El enlace no corresponde a un perfil.")

    return usuario.lower()


def normalizar_perfil_instagram(perfil: dict) -> dict:
    """
    Transforma la respuesta de Apify en métricas
    relevantes para Forge A&R.
    """

    if not isinstance(perfil, dict):
        raise ValueError("La respuesta de Instagram no es válida.")

    usuario = perfil.get("username")
    seguidores = perfil.get("followersCount")

    if not usuario or not isinstance(seguidores, int):
        raise ValueError(
            "El perfil no contiene las métricas obligatorias."
        )

    if perfil.get("private") is True:
        raise ValueError(
            "No se pueden analizar perfiles privados."
        )

    publicaciones = []

    for post in perfil.get("latestPosts") or []:
        if not isinstance(post, dict):
            continue

        likes = post.get("likesCount")
        comentarios = post.get("commentsCount")

        if not isinstance(likes, int) or not isinstance(comentarios, int):
            continue

        propietario = post.get("ownerUsername")

        publicaciones.append({
            "id": post.get("id"),
            "likes": likes,
            "comentarios": comentarios,
            "fecha": post.get("timestamp"),
            "fijada": post.get("isPinned", False),
            "propietario": propietario,
            "es_propia": (
                propietario.lower() == usuario.lower()
                if isinstance(propietario, str)
                else None
            )
        })

    return {
        "instagram_id": str(perfil.get("id")),
        "username": usuario,
        "url": perfil.get("url"),
        "seguidores": seguidores,
        "publicaciones_totales": perfil.get("postsCount"),
        "publicaciones_recuperadas": len(publicaciones),
        "publicaciones": publicaciones,
        "fuente": "Apify Instagram Profile Scraper",
        "estado_metricas": "actualizadas"
    }


async def obtener_metricas_instagram(instagram_url: str) -> dict:
    """
    Obtiene y normaliza las métricas de un perfil
    público de Instagram mediante Apify.
    """

    # 1. Validar el enlace y extraer el usuario.
    usuario = extraer_usuario_instagram(instagram_url)

    # 2. Consultar el perfil en Apify.
    perfil = await consultar_perfil_instagram(usuario)

    # 3. Transformar los datos al formato de Forge A&R.
    metricas = normalizar_perfil_instagram(perfil)

    # 4. Registrar cuándo se obtuvieron las métricas.
    metricas["fecha_obtencion"] = datetime.now(
        timezone.utc
    ).isoformat()

    return metricas
