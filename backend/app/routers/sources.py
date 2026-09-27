"""信源采集通道管理。"""
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Source, User
from ..schemas import SourceUpdate
from ..serializers import source_to_dict

router = APIRouter(prefix="/api/sources", tags=["信源"])


@router.get("")
def list_sources(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    sources = db.query(Source).order_by(Source.id).all()
    return [source_to_dict(s) for s in sources]


@router.put("/{source_id}")
def update_source(source_id: int, body: SourceUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    source = db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="信源不存在")
    if body.enabled is not None:
        source.enabled = body.enabled
    if body.config is not None:
        source.config = json.dumps(body.config, ensure_ascii=False)
    db.commit()
    db.refresh(source)
    return source_to_dict(source)
