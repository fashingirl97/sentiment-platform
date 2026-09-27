"""FastAPI 通用依赖：当前用户解析。"""
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session

from .database import get_db
from .models import User
from .security import decode_token


def get_current_user(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
) -> User:
    """从 Authorization 头解析当前登录用户。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录或凭证缺失")
    token = authorization[7:]
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="凭证无效或已过期")
    user = db.get(User, payload.get("sub"))
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user
