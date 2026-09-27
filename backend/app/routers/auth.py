"""认证路由。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import User
from ..schemas import LoginRequest
from ..security import create_token, verify_password
from ..serializers import user_to_dict

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_token(user.id, user.username, user.role)
    return {"token": token, "username": user.username, "name": user.name, "role": user.role}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return user_to_dict(user)
