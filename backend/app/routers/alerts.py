"""预警告警：列表筛选与处置流转。"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Alert, Disposition, Event, User
from ..schemas import AlertDispositionRequest
from ..serializers import alert_to_dict, disposition_to_dict

router = APIRouter(prefix="/api/alerts", tags=["预警告警"])


@router.get("")
def list_alerts(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    level: str | None = None,
    status: str | None = None,
    event_id: int | None = None,
):
    q = db.query(Alert)
    if level:
        q = q.filter(Alert.level == level)
    if status:
        q = q.filter(Alert.status == status)
    if event_id:
        q = q.filter(Alert.event_id == event_id)
    alerts = q.order_by(Alert.created_at.desc()).all()
    return [alert_to_dict(a) for a in alerts]


@router.post("/{alert_id}/disposition")
def disposition(alert_id: int, body: AlertDispositionRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="告警不存在")
    alert.status = body.action
    if body.action in ("resolved", "ignored"):
        alert.notified_at = datetime.now()

    # 记录处置（联动事件）
    action_map = {"resolved": "已处理", "ignored": "忽略", "processing": "跟踪"}
    record = Disposition(
        event_id=alert.event_id,
        alert_id=alert.id,
        action=action_map.get(body.action, "跟踪"),
        note=body.note,
        operator=user.name,
    )
    db.add(record)
    if alert.event_id and body.action in ("resolved", "ignored"):
        event = db.get(Event, alert.event_id)
        if event:
            event.status = "closed" if body.action == "resolved" else "monitoring"
    db.commit()
    return disposition_to_dict(record)
