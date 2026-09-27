"""预警引擎：告警规则匹配与通知下发（模拟）。"""
from datetime import datetime, timedelta

from ..models import Alert, Post
from .nlp import detect_high_risk, risk_level_from_heat


def evaluate_post_alerts(db, post: Post, configs: dict) -> list[Alert]:
    """对单条舆情内容执行预警规则匹配，返回触发的告警列表。"""
    alerts = []
    hits = detect_high_risk(post.content + (post.ocr_text or "") + (post.asr_text or ""))

    # 规则 1：命中高危敏感词
    if hits:
        alerts.append(Alert(
            event_id=post.event_id,
            post_id=post.id,
            type="高危敏感词",
            level=risk_level_from_heat(post.heat_index),
            title=f"命中高危敏感词：{'、'.join(hits[:3])}",
            content=f"内容「{post.content[:60]}」命中高危敏感词，来源 {post.platform} @{post.author}",
        ))

    # 规则 2：高权重账号（KOL）发声且情绪负向
    if post.author_type == "kol" and post.sentiment == "negative":
        alerts.append(Alert(
            event_id=post.event_id,
            post_id=post.id,
            type="高权重账号发声",
            level=risk_level_from_heat(post.heat_index),
            title=f"KOL「{post.author}」发布负面内容",
            content=f"意见领袖 {post.author} 在 {post.platform} 发布负面内容，互动量 {post.like_count + post.comment_count + post.share_count}",
        ))

    # 规则 3：单小时负向舆情声量环比激增
    surge_alert = _check_volume_surge(db, post, configs)
    if surge_alert:
        alerts.append(surge_alert)

    return alerts


def _check_volume_surge(db, post: Post, configs: dict) -> Alert | None:
    """检查当前小时负向舆情声量是否环比激增超过阈值。"""
    threshold = float(configs.get("negative_surge_threshold", 2.0))
    now = post.publish_time or datetime.now()
    hour_start = now.replace(minute=0, second=0, microsecond=0)
    prev_hour_start = hour_start - timedelta(hours=1)

    current_neg = db.query(Post).filter(
        Post.sentiment == "negative",
        Post.publish_time >= hour_start,
    ).count()
    prev_neg = db.query(Post).filter(
        Post.sentiment == "negative",
        Post.publish_time >= prev_hour_start,
        Post.publish_time < hour_start,
    ).count()

    if prev_neg > 0 and current_neg >= prev_neg * threshold:
        return Alert(
            event_id=post.event_id,
            post_id=post.id,
            type="负向声量激增",
            level="A",
            title=f"负向声量环比激增 {current_neg - prev_neg} 条",
            content=f"近 1 小时负向舆情 {current_neg} 条，环比上一小时（{prev_neg} 条）激增，超过阈值 {threshold} 倍",
        )
    return None
