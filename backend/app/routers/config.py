"""系统运行配置（预警阈值 / 通知渠道 / LLM 参数）。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Config, User
from ..schemas import ConfigUpdate
from ..serializers import config_to_dict

router = APIRouter(prefix="/api/configs", tags=["系统配置"])


@router.get("")
def list_configs(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    configs = db.query(Config).order_by(Config.id).all()
    return [config_to_dict(c) for c in configs]


@router.put("/{key}")
def update_config(key: str, body: ConfigUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    config = db.query(Config).filter(Config.key == key).first()
    if not config:
        config = Config(key=key, value=body.value, description=body.description)
        db.add(config)
    else:
        config.value = body.value
        config.description = body.description or config.description
    db.commit()
    db.refresh(config)
    return config_to_dict(config)
