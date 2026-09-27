"""数据模型定义：覆盖舆情平台全部业务实体。"""
import json
from datetime import datetime

from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String, Text)
from sqlalchemy.orm import relationship

from .database import Base


def now():
    return datetime.now()


class User(Base):
    """系统用户（舆情分析师 / 公关运营 / 系统管理员）。"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    name = Column(String(50), nullable=False)          # 真实姓名
    role = Column(String(20), nullable=False)          # analyst / pr / admin
    created_at = Column(DateTime, default=now)


class Topic(Base):
    """监测主题与关键词包。"""
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, default="")
    keywords = Column(Text, default="[]")              # JSON 数组字符串
    status = Column(String(20), default="active")      # active / paused
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=now)


class Source(Base):
    """信源采集通道。"""
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    type = Column(String(20), nullable=False)          # social / news / video / forum
    enabled = Column(Boolean, default=True)
    config = Column(Text, default="{}")                # JSON 配置


class Post(Base):
    """舆情内容（含多模态解析结果）。"""
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True, index=True)

    title = Column(String(200), default="")
    content = Column(Text, default="")
    author = Column(String(100), default="")
    author_type = Column(String(20), default="normal")  # kol / normal / water
    platform = Column(String(30), default="")
    publish_time = Column(DateTime, default=now, index=True)
    url = Column(String(300), default="")

    # 多模态解析结果
    images = Column(Text, default="[]")                # 图片 URL 数组
    ocr_text = Column(Text, default="")                # 图片 OCR 文本
    asr_text = Column(Text, default="")                # 音视频转录文本

    # 互动数据
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)

    # 分析结果
    sentiment = Column(String(10), default="neutral")  # positive / neutral / negative
    emotion = Column(String(20), default="")           # 愤怒 / 失望 / 恐慌 / 质疑 / 无
    risk_level = Column(String(5), default="C")        # S / A / B / C
    heat_index = Column(Float, default=0.0)            # 舆情烈度指数
    simhash = Column(String(64), default="")           # SimHash 指纹
    entity_names = Column(Text, default="[]")          # 抽取实体名数组
    is_duplicate = Column(Boolean, default=False)      # 是否被去重
    dedup_of = Column(Integer, nullable=True)          # 与哪条内容重复

    created_at = Column(DateTime, default=now)


class Event(Base):
    """聚合舆情事件主题。"""
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    title = Column(String(200), nullable=False)
    summary = Column(Text, default="")
    category = Column(String(30), default="质量争议")   # 质量争议 / 服务纠纷 / 合规风险
    risk_level = Column(String(5), default="C")
    status = Column(String(20), default="monitoring")  # monitoring / alerting / handling / closed
    heat_index = Column(Float, default=0.0)
    sentiment_negative_ratio = Column(Float, default=0.0)
    total_volume = Column(Integer, default=0)

    first_post_id = Column(Integer, nullable=True)
    first_source = Column(String(50), default="")
    first_time = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=now)


class OpinionCluster(Base):
    """核心观点聚类。"""
    __tablename__ = "opinion_clusters"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), index=True)
    label = Column(String(100), nullable=False)
    summary = Column(Text, default="")
    intent = Column(String(50), default="")             # 公众诉求意图
    count = Column(Integer, default=0)
    sentiment = Column(String(10), default="neutral")
    representative_text = Column(Text, default="")


class Entity(Base):
    """热点实体（机构 / 人物 / 产品 / 事件）。"""
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(20), default="产品")           # 机构 / 人物 / 产品 / 事件
    weight = Column(Integer, default=1)


class GraphEdge(Base):
    """实体关系边。"""
    __tablename__ = "graph_edges"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), index=True)
    source = Column(String(100), nullable=False)
    target = Column(String(100), nullable=False)
    relation = Column(String(100), default="关联")
    weight = Column(Integer, default=1)


class TimelineNode(Base):
    """传播溯源时间线节点。"""
    __tablename__ = "timeline_nodes"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), index=True)
    post_id = Column(Integer, nullable=True)
    node_type = Column(String(20), default="扩散")      # 首发 / 引爆 / 扩散
    time = Column(DateTime, default=now)
    title = Column(String(200), default="")
    description = Column(Text, default="")
    author = Column(String(100), default="")
    platform = Column(String(30), default="")
    influence = Column(Integer, default=0)             # 该节点影响力/互动量


class Alert(Base):
    """预警告警。"""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), index=True)
    post_id = Column(Integer, nullable=True)
    type = Column(String(30), default="高危敏感词")    # 负向激增 / 高危敏感词 / 高权重账号发声
    level = Column(String(5), default="A")
    title = Column(String(200), default="")
    content = Column(Text, default="")
    status = Column(String(20), default="pending")      # pending / processing / resolved / ignored
    created_at = Column(DateTime, default=now, index=True)
    notified_at = Column(DateTime, nullable=True)


class Disposition(Base):
    """处置协同记录。"""
    __tablename__ = "dispositions"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), index=True)
    alert_id = Column(Integer, nullable=True)
    action = Column(String(20), default="跟踪")         # 跟踪 / 已核实 / 辟谣处理 / 忽略 / 已处理
    note = Column(Text, default="")
    draft_response = Column(Text, default="")           # 大模型生成的回应草案
    operator = Column(String(50), default="")
    created_at = Column(DateTime, default=now)


class Report(Base):
    """舆情研判报告。"""
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    type = Column(String(20), default="special")        # periodic / special
    event_id = Column(Integer, nullable=True)
    content_md = Column(Text, default="")
    status = Column(String(20), default="draft")
    created_by = Column(String(50), default="")
    created_at = Column(DateTime, default=now)


class Config(Base):
    """系统运行配置（预警阈值 / 通知渠道 / LLM 参数）。"""
    __tablename__ = "configs"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(50), unique=True, nullable=False)
    value = Column(Text, default="")
    description = Column(String(200), default="")
