from fastapi import APIRouter, HTTPException, status

from app.config.database import database
from app.schemas.auth_schema import LoginRequest, TokenResponse
from app.utils.security import verify_password, create_access_token
from app.schemas.user_schema import UserResponse
from app.utils.security import (
    verify_password,
    create_access_token,
    decode_access_token
)

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

bearer_scheme = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    token = credentials.credentials

    try:
        payload = decode_access_token(token)

        user_id = payload.get("sub")

        if not user_id or not ObjectId.is_valid(user_id):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado"
        )

    user = await database.users.find_one(
        {"_id": ObjectId(user_id)}
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado"
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado"
        )

    return user

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
    "/login",
    response_model=TokenResponse
)
async def login(credentials: LoginRequest):

    email = credentials.email.lower().strip()

    user = await database.users.find_one(
        {"email": email}
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos"
        )

    if not verify_password(
        credentials.password,
        user["password_hash"]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos"
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado"
        )

    access_token = create_access_token({
        "sub": str(user["_id"]),
        "role": user["role"]
    })

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get(
    "/me",
    response_model=UserResponse
)
async def get_me(
    current_user: dict = Depends(get_current_user)
):
    return serialize_user(current_user)