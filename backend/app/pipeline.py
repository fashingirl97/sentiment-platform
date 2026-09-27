"""舆情数据接入流水线：清洗 → 情感/情绪/风险分析 → SimHash 去重 → 预警。"""
import json
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .core.alert import evaluate_post_alerts
from .core.graph import extract_entities
from .core.nlp import analyze_sentiment, compute_heat_index, detect_high_risk, risk_level_from_heat
from .core.simhash import compute_simhash, hamming_distance, simhash_hex
from .models import Alert, Post

# 内存 SimHash 去重索引（进程内）
_seen_fps: dict[int, int] = {}


def reset_dedup_index():
    global _seen_fps
    _seen_fps = {}


def analyze_post(db: Session, raw: dict) -> Post:
    """对一条原始舆情内容执行完整分析流水线并落库。"""
    full_text = raw.get("content", "") + (raw.get("ocr_text") or "") + (raw.get("asr_text") or "")

    # 1. 情感与情绪识别
    sent_info = analyze_sentiment(full_text)
    # 2. 高危敏感词
    hits = detect_high_risk(full_text)
    # 3. 舆情烈度与风险等级
    heat = compute_heat_index(
        sentiment=sent_info["sentiment"],
        emotion=sent_info["emotion"],
        like=raw.get("like", 0),
        comment=raw.get("comment", 0),
        share=raw.get("share", 0),
        author_type=raw.get("author_type", "normal"),
        high_risk_hits=len(hits),
    )
    risk = risk_level_from_heat(heat)

    # 4. SimHash 指纹 + 去重
    fp = compute_simhash(raw.get("content", ""))
    is_dup = False
    for existing_fp in _seen_fps:
        if hamming_distance(fp, existing_fp) <= 3:
            is_dup = True
            break
    if not is_dup:
        _seen_fps[fp] = 1

    # 5. 实体抽取
    entities = extract_entities(full_text, raw.get("author", ""), raw.get("author_type", "normal"))
    entity_names = [name for name, _ in entities]

    publish_time = datetime.now() - timedelta(hours=raw.get("hours_ago", 0))

    post = Post(
        topic_id=raw.get("topic_id"),
        source_id=raw.get("source_id"),
        event_id=raw.get("event_id"),
        title=raw.get("title", raw.get("content", "")[:30]),
        content=raw.get("content", ""),
        author=raw.get("author", ""),
        author_type=raw.get("author_type", "normal"),
        platform=raw.get("platform", ""),
        publish_time=publish_time,
        url=raw.get("url", ""),
        images=json.dumps(raw.get("images", []), ensure_ascii=False),
        ocr_text=raw.get("ocr_text", ""),
        asr_text=raw.get("asr_text", ""),
        like_count=raw.get("like", 0),
        comment_count=raw.get("comment", 0),
        share_count=raw.get("share", 0),
        sentiment=sent_info["sentiment"],
        emotion=sent_info["emotion"],
        risk_level=risk,
        heat_index=heat,
        simhash=simhash_hex(fp),
        entity_names=json.dumps(entity_names, ensure_ascii=False),
        is_duplicate=is_dup,
    )
    db.add(post)
    db.flush()  # 取得 post.id

    # 6. 预警规则匹配（仅对非水军、非重复内容）
    if not is_dup and raw.get("author_type") != "water":
        alerts = evaluate_post_alerts(db, post, {})
        for a in alerts:
            db.add(a)

    return post
