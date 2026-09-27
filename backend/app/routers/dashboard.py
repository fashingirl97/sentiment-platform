"""态势大盘：核心指标、声量趋势、情感分布、实时预警、热点词云。"""
from collections import Counter, defaultdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Alert, Event, Post, User
from ..serializers import alert_to_dict
from ..core.simhash import tokenize

router = APIRouter(prefix="/api/dashboard", tags=["态势大盘"])

# 停用词
STOP_WORDS = set("的 了 是 在 我 有 和 就 不 人 都 一 一个 上 也 很 到 说 要 去 你 会 着 没有 看 好 这 那 该 这个 那个 什么 怎么 因为 所以 但是 然后 现在 已经 真的 太 非常 觉得 感觉 大家 你们 我们 他们 就是 还是 不是 只是 还有 如果 可以 应该 需要 希望 让 给 对 于 与 或 及 等 被 把 从 向 为 以 通过 进行 表示 称 网友 用户 网友称 用户称 评论 留言 视频 图片".split())


@router.get("/overview")
def overview(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    posts = db.query(Post).all()
    total = len(posts)
    today = datetime.now().date()
    today_count = sum(1 for p in posts if p.publish_time and p.publish_time.date() == today)
    neg = sum(1 for p in posts if p.sentiment == "negative")
    active_events = db.query(Event).filter(Event.status.in_(["monitoring", "alerting", "handling"])).count()
    high_risk = db.query(Alert).filter(Alert.level.in_(["S", "A"]), Alert.status == "pending").count()
    return {
        "total_volume": total,
        "today_volume": today_count,
        "negative_ratio": round(neg / total * 100, 1) if total else 0,
        "active_events": active_events,
        "high_risk_alerts": high_risk,
        "total_events": db.query(Event).count(),
    }


@router.get("/trend")
def trend(hours: int = 24, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """按小时聚合声量趋势（正/中/负 + 总量）。"""
    since = datetime.now() - timedelta(hours=hours)
    posts = db.query(Post).filter(Post.publish_time >= since).all()
    buckets = defaultdict(lambda: {"positive": 0, "neutral": 0, "negative": 0})
    for p in posts:
        if p.publish_time:
            key = p.publish_time.strftime("%m-%d %H:00")
            buckets[key][p.sentiment] += 1
    result = []
    for key in sorted(buckets.keys()):
        b = buckets[key]
        result.append({"time": key, "total": sum(b.values()), **b})
    return result


@router.get("/sentiment")
def sentiment(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    posts = db.query(Post).all()
    c = Counter(p.sentiment for p in posts)
    total = len(posts)
    return [
        {"name": "正向", "value": c.get("positive", 0), "ratio": round(c.get("positive", 0) / total * 100, 1) if total else 0},
        {"name": "中性", "value": c.get("neutral", 0), "ratio": round(c.get("neutral", 0) / total * 100, 1) if total else 0},
        {"name": "负向", "value": c.get("negative", 0), "ratio": round(c.get("negative", 0) / total * 100, 1) if total else 0},
    ]


@router.get("/risk-alerts")
def risk_alerts(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    alerts = db.query(Alert).order_by(Alert.created_at.desc()).limit(20).all()
    return [alert_to_dict(a) for a in alerts]


@router.get("/hot-words")
def hot_words(limit: int = 50, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    posts = db.query(Post).all()
    counter = Counter()
    for p in posts:
        for tok in tokenize(p.content):
            if tok not in STOP_WORDS and len(tok) >= 2:
                counter[tok] += 1
    return [{"name": w, "value": c} for w, c in counter.most_common(limit)]
