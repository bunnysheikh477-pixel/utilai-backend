from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.database import get_database
from app.core.security import verify_token
from app.models.enums import UserRole
from app.utils.helpers import serialize

security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    if not credentials:
        return None
    user_id = verify_token(credentials.credentials)
    if not user_id:
        return None
    user = serialize(await get_database()["users"].find_one({"_id": user_id, "is_active": True}))
    return user


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> dict:
    user = await get_current_user_optional(credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


async def get_super_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != UserRole.SUPER_ADMIN.value:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
