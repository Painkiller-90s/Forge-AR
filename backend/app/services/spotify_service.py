
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from datetime import datetime, timezone
import re
from urllib.parse import urlparse


# Cargar las credenciales privadas del backend.
ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ENV_PATH)


async def obtener_token_spotify() -> str:
    """Solicita un token de acceso a Spotify mediante Client Credentials."""

    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise RuntimeError(
            "Faltan las credenciales de Spotify en backend/.env"
        )

    async with httpx.AsyncClient(timeout=15.0) as client:
        respuesta = await client.post(
            "https://accounts.spotify.com/api/token",
            auth=(client_id, client_secret),
            data={"grant_type": "client_credentials"},
        )

    if respuesta.status_code != 200:
        raise RuntimeError(
            f"Spotify rechazó la autenticación "
            f"(HTTP {respuesta.status_code})"
        )

    token = respuesta.json().get("access_token")

    if not token:
        raise RuntimeError(
            "Spotify no entregó un token de acceso."
        )

    return token


async def buscar_artistas_spotify(nombre: str) -> list[dict]:
    """Busca artistas en Spotify utilizando la Web API oficial."""

    token = await obtener_token_spotify()

    async with httpx.AsyncClient(timeout=15.0) as client:
        respuesta = await client.get(
            "https://api.spotify.com/v1/search",
            headers={
                "Authorization": f"Bearer {token}",
            },
            params={
                "q": nombre,
                "type": "artist",
                "limit": 5,
            },
        )

    if respuesta.status_code != 200:
        raise RuntimeError(
            f"Error al buscar artistas en Spotify: "
            f"HTTP {respuesta.status_code}"
        )

    datos = respuesta.json()
    artistas = datos.get("artists", {}).get("items", [])

    return [
        {
            "spotify_id": artista.get("id"),
            "nombre": artista.get("name"),
            "url": artista.get("external_urls", {}).get("spotify"),
        }
        for artista in artistas
    ]

async def consultar_artista_spotify(spotify_id: str) -> dict:
    """Consulta los datos disponibles de un artista en Spotify."""

    token = await obtener_token_spotify()

    async with httpx.AsyncClient(timeout=15.0) as client:
        respuesta = await client.get(
            f"https://api.spotify.com/v1/artists/{spotify_id}",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

    if respuesta.status_code != 200:
        raise RuntimeError(
            f"Error al consultar artista: HTTP {respuesta.status_code}"
        )

    datos = respuesta.json()

    return {
        "spotify_id": datos.get("id"),
        "nombre": datos.get("name"),
        "url": datos.get("external_urls", {}).get("spotify"),
        "seguidores": (datos.get("followers") or {}).get("total"),
        "popularidad": datos.get("popularity"),
        "generos": datos.get("genres"),
        "campos_disponibles": sorted(datos.keys()),
        "fuente": "Spotify Web API",
        "fecha_obtencion": datetime.now(timezone.utc).isoformat(),
    }


async def consultar_catalogo_spotify(spotify_id: str) -> dict:
    """Consulta los lanzamientos disponibles del artista en Spotify."""

    token = await obtener_token_spotify()

    async with httpx.AsyncClient(timeout=15.0) as client:
        respuesta = await client.get(
            f"https://api.spotify.com/v1/artists/{spotify_id}/albums",
            headers={
                "Authorization": f"Bearer {token}",
            },
            params={
                "include_groups": "album,single",
                "market": "CL",
                "limit": 5,
            },
        )

    if respuesta.status_code != 200:
        raise RuntimeError(
            f"Error al consultar catálogo: HTTP {respuesta.status_code}"
        )

    datos = respuesta.json()

    return {
        "spotify_id": spotify_id,
        "total_lanzamientos": datos.get("total"),
        "lanzamientos": [
            {
                "nombre": album.get("name"),
                "tipo": album.get("album_type"),
                "fecha_lanzamiento": album.get("release_date"),
            }
            for album in datos.get("items", [])
        ],
        "mercado": "CL",
        "fuente": "Spotify Web API",
        "fecha_obtencion": datetime.now(timezone.utc).isoformat(),
    }


def extraer_id_artista_spotify(spotify_url: str) -> str:
    """Extrae y valida el ID de un perfil de artista de Spotify."""

    if not spotify_url or not isinstance(spotify_url, str):
        raise ValueError("No se proporcionó un enlace de Spotify.")

    url = urlparse(spotify_url.strip())

    if url.scheme != "https" or url.hostname != "open.spotify.com":
        raise ValueError("El enlace no corresponde a Spotify.")

    partes = url.path.strip("/").split("/")

    if (
        len(partes) != 2
        or partes[0] != "artist"
        or not re.fullmatch(r"[A-Za-z0-9]{22}", partes[1])
    ):
        raise ValueError(
            "El enlace debe corresponder a un perfil de artista."
        )

    return partes[1]

