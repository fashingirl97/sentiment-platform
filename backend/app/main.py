"""FastAPI 应用入口。"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import seed
from .database import Base, SessionLocal, engine
from .models import User
from .routers import (alerts, auth, config, dashboard, events, posts, reports,
                      sources, topics)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库结构；空库时自动写入演示数据
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            seed.init_db()
    finally:
        db.close()
    yield


app = FastAPI(title="舆情分析平台", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载路由
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(topics.router)
app.include_router(sources.router)
app.include_router(posts.router)
app.include_router(events.router)
app.include_router(alerts.router)
app.include_router(reports.router)
app.include_router(config.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "name": "舆情分析平台"}
