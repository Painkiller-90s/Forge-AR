
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.config.database import database
from app.routes.auth_route import require_admin


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

    return registros
