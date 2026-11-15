
from fastapi import APIRouter, Depends, HTTPException, Query, status
from bson import ObjectId

from app.config.database import database
from app.routes.auth_route import require_admin


router = APIRouter(
    prefix="/auditorias",
    tags=["Auditorías"]
)


@router.get("/")
async def listar_auditorias(
    pagina: int = Query(default=1, ge=1),
    por_pagina: int = Query(default=20, ge=1, le=100),
    accion: str | None = Query(
        default=None,
        min_length=1,
        max_length=100
    ),
    current_user: dict = Depends(require_admin),
):
    """
    Consulta las auditorías del sello del administrador.

    Permite:
    - Consultar todas las categorías.
    - Filtrar por tipo de acción.
    - Recorrer todos los registros mediante paginación.
    - Obtener estadísticas por tipo de auditoría.
    """

    # 1. Validar sello del administrador.
    sello_id = current_user.get("label_id")

    if not isinstance(sello_id, str) or not sello_id.strip():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El administrador no tiene un sello asignado."
        )

    sello_id = sello_id.strip()

    filtro_sello = {
        "sello_id": sello_id
    }

    filtro = dict(filtro_sello)

    # 2. Aplicar filtro opcional por acción.
    if accion:
        filtro["accion"] = accion

    # 3. Contabilizar los registros.
    total_general = await database.auditorias.count_documents(
        filtro_sello
    )

    total = await database.auditorias.count_documents(
        filtro
    )

    # 4. Obtener cantidades por categoría.
    resumen = {}

    cursor_resumen = await database.auditorias.aggregate([
        {
            "$match": filtro_sello
        },
        {
            "$group": {
                "_id": "$accion",
                "cantidad": {
                    "$sum": 1
                }
            }
        }
    ])

    async for item in cursor_resumen:
        nombre_accion = item.get("_id")

        if nombre_accion:
            resumen[nombre_accion] = item["cantidad"]

    # 5. Consultar la página solicitada.
    desplazamiento = (pagina - 1) * por_pagina

    cursor = (
        database.auditorias
        .find(filtro)
        .sort([
            ("fecha", -1),
            ("_id", -1)
        ])
        .skip(desplazamiento)
        .limit(por_pagina)
    )

    registros = []

    async for registro in cursor:
        registro["id"] = str(registro.pop("_id"))
        registros.append(registro)

    # 6. Recuperar nombres de usuarios del mismo sello.
    ids_usuarios = {
        ObjectId(registro["usuario_id"])
        for registro in registros
        if isinstance(registro.get("usuario_id"), str)
        and ObjectId.is_valid(registro["usuario_id"])
    }

    nombres_usuarios = {}

    if ids_usuarios:
        cursor_usuarios = database.users.find(
            {
                "_id": {
                    "$in": list(ids_usuarios)
                },
                "label_id": sello_id
            },
            {
                "name": 1
            }
        )

        async for usuario in cursor_usuarios:
            nombres_usuarios[str(usuario["_id"])] = (
                usuario.get("name")
            )

    for registro in registros:
        registro["usuario_nombre"] = nombres_usuarios.get(
            registro.get("usuario_id")
        )

    # 7. Calcular páginas disponibles.
    total_paginas = (
        (total + por_pagina - 1) // por_pagina
        if total > 0
        else 0
    )

    return {
        "items": registros,
        "total": total,
        "total_general": total_general,
        "pagina": pagina,
        "por_pagina": por_pagina,
        "total_paginas": total_paginas,
        "resumen": resumen
    }
