from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router

app = FastAPI(title="AI Shopping Assistant")
app.include_router(router)

# 允许跨域
origins = [
    "http://localhost:5173",  # 前端 Vite 默认端口
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # 允许的源
    allow_credentials=True,
    allow_methods=["*"],        # 允许所有 HTTP 方法
    allow_headers=["*"]         # 允许所有请求头
)

@app.get("/")
def root():
    return {"message": "AI Shopping Assistant is running!"}