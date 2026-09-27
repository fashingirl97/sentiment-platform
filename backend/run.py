"""后端启动脚本：uvicorn 启动 FastAPI 服务。"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
