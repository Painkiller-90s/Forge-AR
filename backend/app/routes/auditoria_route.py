
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.config.database import database
from app.routes.auth_route import require_admin
from bson import ObjectId


router = APIRouter(
    prefix="/auditorias",
    tags=["Auditorías"]
)


@router.get("/")
async def listar_auditorias(
    limite: int = Query(default=50, ge=1, le=100),
    current_user: dict = Depends(require_admin),
):
    """
    Permite al administrador consultar las auditorías
    correspondientes exclusivamente a su sello.
    """

    sello_id = current_user.get("label_id")

    if not sello_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El administrador no tiene un sello asignado"
        )

    registros = []

    cursor = (
        database.auditorias
        .find({"sello_id": sello_id})
        .sort("fecha", -1)
        .limit(limite)
    )


    async for registro in cursor:
        registro["id"] = str(registro.pop("_id"))
        registros.append(registro)

    # Obtener los identificadores válidos de los usuarios auditados.
    ids_usuarios = {
        ObjectId(registro["usuario_id"])
        for registro in registros
        if isinstance(registro.get("usuario_id"), str)
        and ObjectId.is_valid(registro["usuario_id"])
    }

    # Consultar los nombres únicamente dentro del sello autorizado.
    nombres_usuarios = {}

    if ids_usuarios:
        async for usuario in database.users.find(
            {
                "_id": {"$in": list(ids_usuarios)},
                "label_id": sello_id,
            },
            {"name": 1},
        ):
            nombres_usuarios[str(usuario["_id"])] = usuario.get("name")

    # Agregar el nombre a la respuesta sin modificar las auditorías.
    for registro in registros:
        registro["usuario_nombre"] = nombres_usuarios.get(
            registro.get("usuario_id")
        )

    return registros

