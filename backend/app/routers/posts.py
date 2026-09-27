"""舆情动态流：多维筛选与分页、详情（含多模态）、实时接入模拟。"""
import random
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Alert, Post, Source, Topic, User
from ..pipeline import analyze_post
from ..serializers import alert_to_dict, post_to_dict

router = APIRouter(prefix="/api/posts", tags=["舆情动态流"])

# 实时接入模拟内容模板
INGEST_TEMPLATES = [
    "刚刷到星耀 X20 Pro 发热的视频，这么多人反馈，这机子散热是真不行啊。",
    "星耀 X20 Pro 续航太差了，出门必须带充电宝，早知道不买了。",
    "星耀 X20 Pro 又死机了，一个月重启十几次，品控严重堪忧！",
    "星耀 X20 Pro 售后响应挺快，给我免费换新了，服务点赞。",
    "星耀官方固件升级后，我的 X20 Pro 发热明显改善，续航也稳了。",
    "看到星耀 X20 Pro 维权群都几百人了，这事闹大了，监管部门该介入了。",
]


@router.get("")
def list_posts(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    topic_id: int | None = None,
    source_id: int | None = None,
    event_id: int | None = None,
    sentiment: str | None = None,
    risk_level: str | None = None,
    keyword: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    page: int = 1,
    page_size: int = 20,
):
    q = db.query(Post)
    if topic_id:
        q = q.filter(Post.topic_id == topic_id)
    if source_id:
        q = q.filter(Post.source_id == source_id)
    if event_id:
        q = q.filter(Post.event_id == event_id)
    if sentiment:
        q = q.filter(Post.sentiment == sentiment)
    if risk_level:
        q = q.filter(Post.risk_level == risk_level)
    if keyword:
        q = q.filter(or_(Post.content.contains(keyword), Post.title.contains(keyword)))
    if start_time:
        q = q.filter(Post.publish_time >= datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S"))
    if end_time:
        q = q.filter(Post.publish_time <= datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S"))

    total = q.count()
    posts = q.order_by(Post.publish_time.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [post_to_dict(p) for p in posts], "total": total, "page": page, "page_size": page_size}


@router.get("/{post_id}")
def get_post(post_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="内容不存在")
    return post_to_dict(post)


@router.post("/ingest")
def ingest(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """模拟实时接入一条新舆情，走完整分析流水线并触发预警。"""
    sources = db.query(Source).filter(Source.enabled == True).all()
    if not sources:
        raise HTTPException(status_code=400, detail="无可用信源")
    source = random.choice(sources)
    topic = db.query(Topic).first()

    authors = ["热心网友", "手机用户小王", "数码爱好者", "普通消费者", "路人张三"]
    raw = {
        "topic_id": topic.id if topic else None,
        "source_id": source.id,
        "event_id": None,
        "content": random.choice(INGEST_TEMPLATES),
        "author": random.choice(authors),
        "author_type": "normal",
        "platform": source.name,
        "hours_ago": random.uniform(0, 1),
        "like": random.randint(5, 400),
        "comment": random.randint(2, 150),
        "share": random.randint(0, 60),
        "images": [],
        "ocr_text": "",
        "asr_text": "",
    }
    post = analyze_post(db, raw)
    db.commit()
    db.refresh(post)

    # 返回触发的新告警
    alerts = db.query(Alert).filter(Alert.post_id == post.id).all()
    return {"post": post_to_dict(post), "alerts": [alert_to_dict(a) for a in alerts]}
