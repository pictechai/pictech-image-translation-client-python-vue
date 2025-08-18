# backend/app/main.py
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.app.routers import translate
from backend.app import config

app = FastAPI()

# 1. 配置 CORS (跨域)
# 中文备注：这等同于 Java 的 CorsConfig
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 允许所有来源，生产环境建议指定前端地址
    allow_credentials=True,
    allow_methods=["*"], # 允许所有方法
    allow_headers=["*"], # 允许所有头
)

# 2. 包含 API 路由
app.include_router(translate.router)

# 3. 挂载上传文件目录为静态资源
# 中文备注：这样前端才能通过 /uploads/... 访问到保存的图片
# 确保 UPLOAD_DIR 目录存在
os.makedirs(config.UPLOAD_DIR, exist_ok=True)
app.mount(f"/{os.path.basename(config.UPLOAD_DIR)}", StaticFiles(directory=config.UPLOAD_DIR), name="uploads")

# 4. 挂载前端静态文件
# 中文备注：这是关键一步，让 FastAPI 托管 Vue 应用
# 我们假设 Vue 编译后的文件在 ../frontend/dist
# 注意路径是相对于当前 main.py 文件的
frontend_dist_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")

if os.path.exists(frontend_dist_path):
    app.mount("/", StaticFiles(directory=frontend_dist_path, html=True), name="static")

    # 配置一个“捕获所有”的路由，将所有未匹配的路径都指向 index.html
    # 这对于使用 history 模式的 Vue Router至关重要
    @app.get("/{full_path:path}")
    async def serve_vue_app(full_path: str):
        index_path = os.path.join(frontend_dist_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"error": "Frontend not found"}
else:
    print(f"警告：前端编译目录 '{frontend_dist_path}' 不存在。请先编译Vue项目。")