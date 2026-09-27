"""事件研判：详情、观点聚类、实体图谱、传播溯源、处置协同、回应草案。"""
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.clustering import cluster_opinions
from ..core.graph import build_graph, build_timeline
from ..core.llm import generate_response_draft, generate_strategy_suggestion
from ..database import get_db
from ..deps import get_current_user
from ..models import Disposition, Event, Post, User
from ..schemas import DraftResponseRequest, EventDispositionRequest
from ..serializers import disposition_to_dict, event_to_dict

router = APIRouter(prefix="/api/events", tags=["事件研判"])


@router.get("")
def list_events(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    events = db.query(Event).order_by(Event.heat_index.desc()).all()
    result = []
    for e in events:
        d = event_to_dict(e)
        d["post_count"] = db.query(Post).filter(Post.event_id == e.id).count()
        result.append(d)
    return result


@router.get("/{event_id}")
def get_event(event_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="事件不存在")
    posts = db.query(Post).filter(Post.event_id == event_id).all()
    d = event_to_dict(event)
    d["post_count"] = len(posts)
    d["emotion_dist"] = _emotion_distribution(posts)
    return d


@router.get("/{event_id}/clusters")
def get_clusters(event_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    posts = db.query(Post).filter(Post.event_id == event_id).all()
    return cluster_opinions(posts)


@router.get("/{event_id}/graph")
def get_graph(event_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    posts = db.query(Post).filter(Post.event_id == event_id).all()
    nodes, edges = build_graph(event_id, posts)
    return {"nodes": nodes, "edges": edges}


@router.get("/{event_id}/timeline")
def get_timeline(event_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    posts = db.query(Post).filter(Post.event_id == event_id).all()
    return build_timeline(event_id, posts)


@router.get("/{event_id}/dispositions")
def get_dispositions(event_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    records = db.query(Disposition).filter(Disposition.event_id == event_id).order_by(Disposition.created_at.desc()).all()
    return [disposition_to_dict(r) for r in records]


@router.post("/{event_id}/disposition")
def create_disposition(event_id: int, body: EventDispositionRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="事件不存在")

    # 生成回应草案（若为辟谣/已核实/已处理等实质性处置动作）
    draft = ""
    if body.action in ("辟谣处理", "已核实", "已处理"):
        posts = db.query(Post).filter(Post.event_id == event_id).all()
        clusters = cluster_opinions(posts)
        main_emotion = _main_emotion(posts)
        main_intent = clusters[0]["intent"] if clusters else "信息关注"
        draft = generate_response_draft(event.title, event.category, event.risk_level, main_emotion, main_intent)

    record = Disposition(
        event_id=event_id,
        action=body.action,
        note=body.note,
        draft_response=draft,
        operator=user.name,
    )
    db.add(record)

    # 更新事件状态
    if body.action in ("已处理", "忽略"):
        event.status = "closed"
    elif body.action in ("跟踪", "已核实", "辟谣处理"):
        event.status = "handling"
    db.commit()
    db.refresh(record)
    return disposition_to_dict(record)


@router.post("/{event_id}/draft-response")
def draft_response(event_id: int, body: DraftResponseRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="事件不存在")
    posts = db.query(Post).filter(Post.event_id == event_id).all()
    clusters = cluster_opinions(posts)
    main_emotion = _main_emotion(posts)
    main_intent = clusters[0]["intent"] if clusters else "信息关注"
    response = generate_response_draft(event.title, event.category, event.risk_level, main_emotion, main_intent)
    strategy = generate_strategy_suggestion(event.title, event.category, event.risk_level, main_intent)
    return {"response": response, "strategy": strategy}


def _main_emotion(posts: list) -> str:
    c = Counter(p.emotion for p in posts if p.emotion)
    return c.most_common(1)[0][0] if c else "失望"


def _emotion_distribution(posts: list) -> dict:
    c = Counter(p.emotion for p in posts if p.emotion)
    total = len(posts) or 1
    return {k: v for k, v in c.most_common()}
