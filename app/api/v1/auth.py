from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from pymongo.errors import DuplicateKeyError

from app.api.deps import get_current_user
from app.core.database import get_database
from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.utils.helpers import new_id, serialize, utcnow

router = APIRouter()


class RegisterBody(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    full_name: str = Field(min_length=1, max_length=120)


class LoginBody(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


def _public_user(user: dict) -> dict:
    public_user = serialize(user)
    public_user.pop("password_hash", None)
    return public_user


@router.post("/register")
async def register(data: RegisterBody):
    db = get_database()
    email = str(data.email).lower()
    if await db["users"].find_one({"email": email}):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered.",
        )
    user_id = new_id()
    doc = {
        "_id": user_id,
        "email": email,
        "password_hash": hash_password(data.password),
        "full_name": data.full_name.strip(),
        "role": "user",
        "is_active": True,
        "plan": "free",
        "created_at": utcnow(),
    }
    try:
        await db["users"].insert_one(doc)
    except DuplicateKeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered.",
        ) from exc
    tokens = {"access_token": create_access_token(user_id), "refresh_token": create_refresh_token(user_id)}
    return {"success": True, "data": {**tokens, "user": _public_user(doc)}}


@router.post("/login")
async def login(data: LoginBody):
    db = get_database()
    user = await db["users"].find_one({"email": str(data.email).lower()})
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is disabled.",
        )
    uid = str(user["_id"])
    tokens = {"access_token": create_access_token(uid), "refresh_token": create_refresh_token(uid)}
    return {"success": True, "data": {**tokens, "user": _public_user(user)}}


@router.get("/me")
async def me(user=Depends(get_current_user)):
    return {"success": True, "data": user}
