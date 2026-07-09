from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import require_admin
from app.core.database import db
from app.core.security import create_token, verify_password
from app.models.schemas import LoginBody, TokenResp


router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=TokenResp)
async def login(body: LoginBody):
    user = await db.users.find_one({"email": body.email.lower()})
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_token(user["id"], user["email"])
    return TokenResp(
        access_token=token,
        user={
            "id": user["id"],
            "email": user["email"],
            "name": user.get("name"),
            "role": user.get("role"),
        },
    )


@router.get("/auth/me")
async def me(user: dict = Depends(require_admin)):
    return user

