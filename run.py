# run.py
import uvicorn
import os

if __name__ == "__main__":
    # 中文备注：指定 FastAPI 应用的位置，并启用热重载
    # 'backend.app.main:app' 指向 backend/app/main.py 文件中的 app 对象
    uvicorn.run("backend.app.main:app", host="localhost", port=8000, reload=True)