
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.errors import DuplicateKeyError

from app.config.database import database
from app.models.user_model import user_document
from app.schemas.user_schema import (
    UserCreate,
    UserUpdate,
    UserResponse,
)
from app.utils.security import hash_password
from app.routes.auth_route import require_admin


router = APIRouter(
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(require_admin)]
)


def obtener_sello_id(current_user: dict) -> str:
    sello_id = current_user.get("label_id")

    if not isinstance(sello_id, str) or not sello_id.strip():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El administrador no tiene un sello asignado"
        )

    return sello_id.strip()


def serialize_user(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "label_id": user.get("label_id"),
        "is_active": user.get("is_active", True),
    }


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_user(
    user: UserCreate,
    current_user: dict = Depends(require_admin)
):
    sello_id = obtener_sello_id(current_user)

    email = str(user.email).lower().strip()

    existing_user = await database.users.find_one({
        "email": email
    })

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese correo"
        )

    document = user_document(
        name=user.name.strip(),
        email=email,
        password_hash=hash_password(user.password),
        role="ar",
        label_id=sello_id
    )

    try:
        result = await database.users.insert_one(document)

    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese correo"
        )

    created_user = await database.users.find_one({
        "_id": result.inserted_id
    })

    return serialize_user(created_user)


@router.get(
    "/",
    response_model=list[UserResponse]
)
async def get_users(
    current_user: dict = Depends(require_admin)
):
    sello_id = obtener_sello_id(current_user)

    cursor = (
        database.users
        .find({
            "label_id": sello_id,
            "role": "ar"
        })
        .sort("name", 1)
    )

    users = []

    async for user in cursor:
        users.append(serialize_user(user))

    return users


@router.get(
    "/{user_id}",
    response_model=UserResponse
)
async def get_user(
    user_id: str,
    current_user: dict = Depends(require_admin)
):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de usuario inválido"
        )

    sello_id = obtener_sello_id(current_user)

    user = await database.users.find_one({
        "_id": ObjectId(user_id),
        "label_id": sello_id,
        "role": "ar"
    })

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario A&R no encontrado"
        )

    return serialize_user(user)


@router.put(
    "/{user_id}",
    response_model=UserResponse
)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: dict = Depends(require_admin)
):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de usuario inválido"
        )

    sello_id = obtener_sello_id(current_user)

    filtro_usuario = {
        "_id": ObjectId(user_id),
        "label_id": sello_id,
        "role": "ar"
    }

    usuario_actual = await database.users.find_one(
        filtro_usuario
    )

    if not usuario_actual:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario A&R no encontrado"
        )

    update_data = user_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se enviaron datos para actualizar"
        )

    for campo, valor in update_data.items():
        if valor is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El campo {campo} no puede ser nulo"
            )

    if "name" in update_data:
        update_data["name"] = update_data["name"].strip()

        if len(update_data["name"]) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre debe tener al menos 2 caracteres"
            )

    if "email" in update_data:
        update_data["email"] = (
            str(update_data["email"]).lower().strip()
        )

        existing_user = await database.users.find_one({
            "email": update_data["email"],
            "_id": {"$ne": ObjectId(user_id)}
        })

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un usuario con ese correo"
            )

    try:
        result = await database.users.update_one(
            filtro_usuario,
            {"$set": update_data}
        )

    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese correo"
        )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario A&R no encontrado"
        )

    updated_user = await database.users.find_one(
        filtro_usuario
    )

    return serialize_user(updated_user)
