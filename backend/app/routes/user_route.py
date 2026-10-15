from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.config.database import database
from app.models.user_model import user_document
from app.schemas.user_schema import UserCreate, UserUpdate, UserResponse
from app.utils.security import hash_password
from app.routes.auth_route import require_admin
from pymongo.errors import DuplicateKeyError


router = APIRouter(
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(require_admin)]
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
async def create_user(
    user: UserCreate,
    current_user: dict = Depends(require_admin)
):
    sello_id = current_user.get("label_id")

    if not sello_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El administrador no tiene un sello asignado"
        )

    # Impedir que el administrador cree usuarios de otro sello.
    if user.label_id is not None and user.label_id != sello_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes crear usuarios de otro sello"
        )

    existing_user = await database.users.find_one(
        {"email": user.email.lower().strip()}
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese correo"
        )

    hashed_password = hash_password(user.password)

    # El sello lo determina el usuario autenticado.
    document = user_document(
        name=user.name,
        email=user.email,
        password_hash=hashed_password,
        role=user.role,
        label_id=sello_id
    )

    try:
        result = await database.users.insert_one(document)

    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese correo"
        )

    created_user = await database.users.find_one(
        {"_id": result.inserted_id}
    )

    return serialize_user(created_user)



@router.get(
    "/",
    response_model=list[UserResponse]
)
async def get_users(
    current_user: dict = Depends(require_admin)
):
    sello_id = current_user.get("label_id")

    if not sello_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El administrador no tiene un sello asignado"
        )

    users = []

    async for user in database.users.find(
        {"label_id": sello_id}
    ):
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

    sello_id = current_user.get("label_id")

    if not sello_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El administrador no tiene un sello asignado"
        )

    user = await database.users.find_one({
        "_id": ObjectId(user_id),
        "label_id": sello_id
    })

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

    sello_id = current_user.get("label_id")

    if not sello_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El administrador no tiene un sello asignado"
        )

    # Verificar que el usuario pertenezca al sello del administrador.
    filtro_usuario = {
        "_id": ObjectId(user_id),
        "label_id": sello_id
    }

    usuario_actual = await database.users.find_one(
        filtro_usuario
    )

    if not usuario_actual:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    update_data = user_data.model_dump(exclude_unset=True)

    
    # Impedir que el administrador modifique su propio rol o estado.
    if str(current_user["_id"]) == user_id:
        if "role" in update_data or "is_active" in update_data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puedes modificar tu propio rol o estado"
            )


    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se enviaron datos para actualizar"
        )

    # Impedir cambios de sello mediante el endpoint.
    if "label_id" in update_data:
        if update_data["label_id"] != sello_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puedes asignar usuarios a otro sello"
            )

        # El sello del usuario no se modifica.
        update_data.pop("label_id")

    # Impedir valores nulos en campos obligatorios.
    for campo in ("name", "email", "role", "is_active"):
        if campo in update_data and update_data[campo] is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El campo {campo} no puede ser nulo"
            )

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay cambios para actualizar"
        )

    # Normalizar email si se modifica.
    if "email" in update_data:
        update_data["email"] = (
            update_data["email"].lower().strip()
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

    result = await database.users.update_one(
        filtro_usuario,
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    updated_user = await database.users.find_one(
        filtro_usuario
    )

    return serialize_user(updated_user)



@router.delete(
    "/{user_id}",
    status_code=status.HTTP_200_OK
)
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_admin)
):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de usuario inválido"
        )

    sello_id = current_user.get("label_id")

    if not sello_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El administrador no tiene un sello asignado"
        )

    # Impedir que el administrador elimine su propia cuenta.
    if str(current_user["_id"]) == user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes eliminar tu propia cuenta"
        )

    # Eliminar únicamente usuarios del mismo sello.
    result = await database.users.delete_one({
        "_id": ObjectId(user_id),
        "label_id": sello_id
    })

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    return {
        "message": "Usuario eliminado correctamente"
    }
