"""Pydantic 请求/响应模型。"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ---------- 认证 ----------
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    token: str
    username: str
    name: str
    role: str


# ---------- 监测主题 ----------
class TopicCreate(BaseModel):
    name: str
    description: str = ""
    keywords: list[str] = []


class TopicUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[list[str]] = None
    status: Optional[str] = None


# ---------- 信源 ----------
class SourceUpdate(BaseModel):
    enabled: Optional[bool] = None
    config: Optional[dict] = None


# ---------- 舆情内容 ----------
class PostFilter(BaseModel):
    topic_id: Optional[int] = None
    source_id: Optional[int] = None
    sentiment: Optional[str] = None
    risk_level: Optional[str] = None
    event_id: Optional[int] = None
    keyword: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    page: int = 1
    page_size: int = 20


# ---------- 事件 ----------
class EventDispositionRequest(BaseModel):
    action: str                  # 跟踪 / 已核实 / 辟谣处理 / 忽略 / 已处理
    note: str = ""


class AlertDispositionRequest(BaseModel):
    action: str                  # processing / resolved / ignored
    note: str = ""


class DraftResponseRequest(BaseModel):
    event_id: int


# ---------- 报告 ----------
class ReportGenerateRequest(BaseModel):
    event_id: Optional[int] = None
    type: str = "special"        # periodic / special
    title: Optional[str] = None


# ---------- 配置 ----------
class ConfigUpdate(BaseModel):
    key: str
    value: str
    description: str = ""
