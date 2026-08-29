from bson import ObjectId
from fastapi import APIRouter, HTTPException, status

from app.config.database import database
from app.models.user_model import user_document
from app.schemas.user_schema import UserCreate, UserUpdate, UserResponse
from app.utils.security import hash_password


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


def serialize_user(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "label_id": user.get("label_id"),
        "is_active": user["is_active"]
    }


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_user(user: UserCreate):

    existing_user = await database.users.find_one(
        {"email": user.email.lower().strip()}
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese correo"
        )

    hashed_password = hash_password(user.password)

    document = user_document(
        name=user.name,
        email=user.email,
        password_hash=hashed_password,
        role=user.role,
        label_id=user.label_id
    )

    result = await database.users.insert_one(document)

    created_user = await database.users.find_one(
        {"_id": result.inserted_id}
    )

    return serialize_user(created_user)


@router.get(
    "/",
    response_model=list[UserResponse]
)
async def get_users():

    users = []

    async for user in database.users.find():
        users.append(serialize_user(user))

    return users


@router.get(
    "/{user_id}",
    response_model=UserResponse
)
async def get_user(user_id: str):

    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de usuario inválido"
        )

    user = await database.users.find_one(
        {"_id": ObjectId(user_id)}
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    return serialize_user(user)

@router.put(
    "/{user_id}",
    response_model=UserResponse
)
async def update_user(user_id: str, user_data: UserUpdate):

    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de usuario inválido"
        )

    update_data = user_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se enviaron datos para actualizar"
        )

    # Normalizar email si viene en la actualización
    if "email" in update_data:
        update_data["email"] = update_data["email"].lower().strip()

        existing_user = await database.users.find_one({
            "email": update_data["email"],
            "_id": {"$ne": ObjectId(user_id)}
        })

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un usuario con ese correo"
            )

    result = await database.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    updated_user = await database.users.find_one(
        {"_id": ObjectId(user_id)}
    )

    return serialize_user(updated_user)

@router.delete(
    "/{user_id}",
    status_code=status.HTTP_200_OK
)
async def delete_user(user_id: str):

    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de usuario inválido"
        )

    result = await database.users.delete_one(
        {"_id": ObjectId(user_id)}
    )

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    return {
        "message": "Usuario eliminado correctamente"
    }