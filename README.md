
# 📘 图片翻译编辑器 - Python 后端版

本项目是一个前后端分离的应用：

* 前端使用 **Vue.js** 构建
* 后端由 **Java Spring Boot** 迁移至 **Python FastAPI**

FastAPI 后端不仅处理 API 请求，还负责托管编译好的前端静态文件，实现 **一体化部署**。

---

## ✨ 项目特点

* **后端**：Python 3.8+ + FastAPI，高性能异步 API
* **前端**：Vue.js，用户交互界面
* **API 客户端**：内置与第三方 PicTech 图片处理服务的通信客户端
* **一体化部署**：Python 后端直接提供前端静态资源，简化部署流程
* **配置灵活**：使用 `.env` 文件管理敏感配置（API 密钥等）
* **跨域支持**：默认配置了 CORS，方便前后端开发环境分离调试

---

## 📂 项目结构

```bash
/
|-- backend/             # 后端 Python 代码
|   |-- app/             # FastAPI 应用核心
|   |-- venv/            # Python 虚拟环境
|   |-- requirements.txt # Python 依赖
|   `-- .env.example     # 环境变量配置模板
|
|-- frontend/            # 前端 Vue 源代码
|   |-- dist/            # (编译后生成) 静态文件
|   |-- src/             
|   |-- package.json
|   `-- ...
|
|-- uploads/             # (自动生成) 用户上传图片保存目录
|
|-- run.py               # 项目统一启动脚本
|
`-- README.md            # 本文档
```

---

## 🚀 运行指南

### 1️⃣ 先决条件

请确保系统已安装以下软件：

* Python **3.8+**
* Node.js **16.x+**（含 npm）
* Git（可选，用于版本控制）

---

### 2️⃣ 后端配置

#### 2.1 创建并激活虚拟环境

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# macOS / Linux
source venv/bin/activate
# Windows
venv\Scripts\activate
```

#### 2.2 安装依赖

```bash
pip install -r requirements.txt
```

#### 2.3 配置环境变量

复制 `.env.example` 为 `.env`，并填写 PicTech API 信息：

```dotenv
# .env 文件内容
PICOTECH_BASE_URL="http://example.com"
PICOTECH_API_KEY="你的AccountId"
PICOTECH_SECRET="你的SecretKey"

# 文件上传目录
UPLOAD_DIR="uploads"
```

---

### 3️⃣ 前端配置与编译

#### 3.1 安装依赖

```bash
cd frontend
npm install
```

#### 3.2 编译前端

```bash
npm run build
```

编译完成后会在 `frontend/dist/` 生成静态文件。

---

### 4️⃣ 启动应用

返回项目根目录，运行统一脚本：

```bash
cd ..
python run.py
```

启动成功日志示例：

```
INFO:     Started server process [12345]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

### 5️⃣ 访问应用

浏览器打开： [http://localhost:8000](http://localhost:8000)
你将看到 Vue 前端界面，所有 API 请求由 FastAPI 后端处理。

---

## 💡 开发模式提示

* **后端热重载**：`run.py` 已开启热重载，修改后端代码会自动重启服务
* **前端热重载**：在 `frontend/` 下执行

```bash
npm run serve
```

Vue 开发服务默认运行在 [http://localhost:8080](http://localhost:8080)。

若需避免跨域，请在 `vue.config.js` 添加代理，将 `/api` 转发到 `http://localhost:8000`。

---
