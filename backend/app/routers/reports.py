"""研判报告：生成、列表、详情。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.report import build_event_report
from ..database import get_db
from ..deps import get_current_user
from ..models import Disposition, Event, Post, Report, Source, User
from ..schemas import ReportGenerateRequest
from ..serializers import report_to_dict

router = APIRouter(prefix="/api/reports", tags=["研判报告"])


@router.get("")
def list_reports(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    reports = db.query(Report).order_by(Report.created_at.desc()).all()
    return [report_to_dict(r) for r in reports]


@router.post("/generate")
def generate(body: ReportGenerateRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if body.type == "special":
        if not body.event_id:
            raise HTTPException(status_code=400, detail="专项报告需要指定事件")
        event = db.get(Event, body.event_id)
        if not event:
            raise HTTPException(status_code=404, detail="事件不存在")
        posts = db.query(Post).filter(Post.event_id == event.id).all()
        clusters = __import__("app.core.clustering", fromlist=["cluster_opinions"]).cluster_opinions(posts)
        timeline = __import__("app.core.graph", fromlist=["build_timeline"]).build_timeline(event.id, posts)
        dispositions = db.query(Disposition).filter(Disposition.event_id == event.id).all()
        sources = db.query(Source).filter(Source.id.in_([p.source_id for p in posts if p.source_id])).all()
        content = build_event_report(event, posts, clusters, timeline, dispositions, sources)
        title = body.title or f"{event.title} 舆情专项研判报告"
    else:
        # 周期性简报：汇总全部活跃事件
        events = db.query(Event).all()
        parts = ["# 舆情周期性监测简报\n"]
        for e in events:
            posts = db.query(Post).filter(Post.event_id == e.id).all()
            neg = sum(1 for p in posts if p.sentiment == "negative")
            parts.append(f"## {e.title}\n")
            parts.append(f"- 风险等级：{e.risk_level} | 声量：{len(posts)} | 负面率：{round(neg/len(posts)*100,1) if posts else 0}%")
            parts.append("")
        content = "\n".join(parts)
        title = body.title or "舆情周期性监测简报"

    report = Report(title=title, type=body.type, event_id=body.event_id, content_md=content, created_by=user.name)
    db.add(report)
    db.commit()
    db.refresh(report)
    return report_to_dict(report)


@router.get("/{report_id}")
def get_report(report_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    return report_to_dict(report)


@router.delete("/{report_id}")
def delete_report(report_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    db.delete(report)
    db.commit()
    return {"ok": True}
