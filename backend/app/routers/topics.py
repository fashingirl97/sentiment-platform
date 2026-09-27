"""监测主题与关键词维护。"""
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Topic, User
from ..schemas import TopicCreate, TopicUpdate
from ..serializers import topic_to_dict

router = APIRouter(prefix="/api/topics", tags=["监测主题"])


@router.get("")
def list_topics(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    topics = db.query(Topic).order_by(Topic.id.desc()).all()
    return [topic_to_dict(t) for t in topics]


@router.post("")
def create_topic(body: TopicCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    topic = Topic(
        name=body.name,
        description=body.description,
        keywords=json.dumps(body.keywords, ensure_ascii=False),
        created_by=user.id,
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic_to_dict(topic)


@router.put("/{topic_id}")
def update_topic(topic_id: int, body: TopicUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    topic = db.get(Topic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="主题不存在")
    if body.name is not None:
        topic.name = body.name
    if body.description is not None:
        topic.description = body.description
    if body.keywords is not None:
        topic.keywords = json.dumps(body.keywords, ensure_ascii=False)
    if body.status is not None:
        topic.status = body.status
    db.commit()
    db.refresh(topic)
    return topic_to_dict(topic)


@router.delete("/{topic_id}")
def delete_topic(topic_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    topic = db.get(Topic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="主题不存在")
    db.delete(topic)
    db.commit()
    return {"ok": True}
