"""ORM 对象 -> dict 序列化辅助。"""
import json


def _loads(text, default):
    try:
        return json.loads(text) if text else default
    except Exception:
        return default


def user_to_dict(u):
    return {"id": u.id, "username": u.username, "name": u.name, "role": u.role}


def topic_to_dict(t):
    return {
        "id": t.id, "name": t.name, "description": t.description,
        "keywords": _loads(t.keywords, []), "status": t.status,
        "created_by": t.created_by, "created_at": _fmt(t.created_at),
    }


def source_to_dict(s):
    return {
        "id": s.id, "name": s.name, "type": s.type,
        "enabled": s.enabled, "config": _loads(s.config, {}),
    }


def post_to_dict(p):
    return {
        "id": p.id, "topic_id": p.topic_id, "source_id": p.source_id, "event_id": p.event_id,
        "title": p.title, "content": p.content, "author": p.author, "author_type": p.author_type,
        "platform": p.platform, "publish_time": _fmt(p.publish_time), "url": p.url,
        "images": _loads(p.images, []), "ocr_text": p.ocr_text, "asr_text": p.asr_text,
        "like_count": p.like_count, "comment_count": p.comment_count, "share_count": p.share_count,
        "sentiment": p.sentiment, "emotion": p.emotion, "risk_level": p.risk_level,
        "heat_index": p.heat_index, "entity_names": _loads(p.entity_names, []),
        "is_duplicate": p.is_duplicate,
    }


def event_to_dict(e):
    return {
        "id": e.id, "topic_id": e.topic_id, "title": e.title, "summary": e.summary,
        "category": e.category, "risk_level": e.risk_level, "status": e.status,
        "heat_index": e.heat_index, "sentiment_negative_ratio": e.sentiment_negative_ratio,
        "total_volume": e.total_volume, "first_post_id": e.first_post_id,
        "first_source": e.first_source, "first_time": _fmt(e.first_time),
        "created_at": _fmt(e.created_at),
    }


def alert_to_dict(a):
    return {
        "id": a.id, "event_id": a.event_id, "post_id": a.post_id, "type": a.type,
        "level": a.level, "title": a.title, "content": a.content, "status": a.status,
        "created_at": _fmt(a.created_at), "notified_at": _fmt(a.notified_at),
    }


def disposition_to_dict(d):
    return {
        "id": d.id, "event_id": d.event_id, "alert_id": d.alert_id, "action": d.action,
        "note": d.note, "draft_response": d.draft_response, "operator": d.operator,
        "created_at": _fmt(d.created_at),
    }


def report_to_dict(r):
    return {
        "id": r.id, "title": r.title, "type": r.type, "event_id": r.event_id,
        "content_md": r.content_md, "status": r.status, "created_by": r.created_by,
        "created_at": _fmt(r.created_at),
    }


def config_to_dict(c):
    return {"id": c.id, "key": c.key, "value": c.value, "description": c.description}


def _fmt(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None
