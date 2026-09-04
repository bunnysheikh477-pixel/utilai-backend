from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, EmailStr

from app.api.deps import get_current_user
from app.core.database import get_database
from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password, verify_token
from app.utils.helpers import new_id, serialize, utcnow

router = APIRouter()


class RegisterBody(BaseModel):
    email: EmailStr
    password: str
    full_name: str = ""


class LoginBody(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
async def register(data: RegisterBody):
    db = get_database()
    if await db["users"].find_one({"email": data.email.lower()}):
        return {"success": False, "message": "Email already registered"}
    user_id = new_id()
    doc = {
        "_id": user_id,
        "email": data.email.lower(),
        "password_hash": hash_password(data.password),
        "full_name": data.full_name,
        "role": "user",
        "is_active": True,
        "plan": "free",
        "created_at": utcnow(),
    }
    await db["users"].insert_one(doc)
    tokens = {"access_token": create_access_token(user_id), "refresh_token": create_refresh_token(user_id)}
    user = serialize(doc)
    return {"success": True, "data": {**tokens, "user": user}}


@router.post("/login")
async def login(data: LoginBody):
    db = get_database()
    user = await db["users"].find_one({"email": data.email.lower()})
    if not user or not verify_password(data.password, user["password_hash"]):
        return {"success": False, "message": "Invalid credentials"}
    uid = str(user["_id"])
    tokens = {"access_token": create_access_token(uid), "refresh_token": create_refresh_token(uid)}
    return {"success": True, "data": {**tokens, "user": serialize(user)}}


@router.get("/me")
async def me(user=Depends(get_current_user)):
    return {"success": True, "data": user}
