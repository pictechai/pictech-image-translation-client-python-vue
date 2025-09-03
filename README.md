# 📘 PicTech 图片翻译编辑器 - Python 后端版

本项目是一个集成了强大在线图片编辑与多语言翻译功能的全栈解决方案。前端使用 Vue.js 构建，提供直观的用户交互界面；后端由 Python FastAPI 驱动，取代了 Java Spring Boot，提供高性能异步 API，并托管编译后的前端静态文件，实现前后端一体化部署。

## ✨ 项目特点
- **前端**：基于 Vue.js，提供响应式、交互式的图片编辑与翻译界面。
- **后端**：Python 3.8+ 与 FastAPI，高效处理异步 API 请求。
- **API 客户端**：内置与第三方 PicTech 图片处理服务的通信客户端。
- **一体化部署**：FastAPI 后端直接提供前端静态资源，简化部署流程。
- **配置灵活**：使用 `.env` 文件管理敏感配置（如 API 密钥）。
- **跨域支持**：默认启用 CORS，方便前后端分离开发与调试。

## 📂 项目结构
```
/                        # 项目根目录
|-- backend/             # 后端 Python 代码
|   |-- app/             # FastAPI 应用核心代码
|   |   |-- main.py      # FastAPI 应用入口
|   |   |-- routes/      # API 路由定义
|   |   |-- services/    # 业务逻辑层
|   |   `-- models/      # 数据模型
|   |-- venv/            # Python 虚拟环境
|   |-- requirements.txt # Python 依赖列表
|   `-- .env.example     # 环境变量配置模板
|
|-- frontend/            # 前端 Vue 源代码
|   |-- dist/            # (编译后生成) 静态文件目录
|   |-- public/          # 静态资源，如 index.html
|   |-- src/             # Vue 应用核心代码
|   |   |-- components/  # Vue 组件
|   |   |   `-- ImageEditor.vue # 核心编辑器组件
|   |   |-- App.vue      # 承载 ImageEditor 的父组件
|   |   `-- main.js      # Vue 应用入口
|   |-- vue.config.js    # Vue CLI 配置文件
|   `-- package.json     # 前端依赖与脚本
|
|-- uploads/             # (自动生成) 用户上传图片保存目录
|
|-- run.py               # 项目统一启动脚本
|
`-- README.md            # 本文档
```

### 📁 前端结构与说明
- **public/**：包含静态资源，如 `index.html`，用于初始化 Vue 应用。
- **src/**：前端 Vue 应用的核心代码。
  - **components/ImageEditor.vue**：核心编辑器组件，负责图片编辑（裁剪、旋转、缩放等）与翻译功能（文本识别、翻译、添加文本）。支持拖拽、画布操作以及实时预览。
  - **App.vue**：父组件，用于承载和演示 `ImageEditor.vue`，并提供界面布局和交互逻辑。
    - **按钮配置**：`App.vue` 的 `data` 中定义了 `myButtonConfig` 对象，用于控制编辑器界面中按钮的显示与隐藏。配置如下：
      ```javascript
      myButtonConfig: {
          upload: true,    // 启用文件上传按钮，允许用户上传图片
          addText: true,   // 启用添加文本按钮，支持在图片上添加翻译文本
          restore: true,   // 启用局部恢复按钮，用于恢复擦除区域
          undo: true,      // 启用撤销按钮，回退上一步操作
          redo: true,      // 启用重做按钮，恢复已撤销的操作
          erase: true,     // 启用擦除按钮，支持擦除图片指定区域
          export: true,    // 启用导出按钮，生成最终图片
          save: true,      // 启用保存按钮，保存当前画布状态
          reset: true      // 启用重置按钮，重置画布到初始状态
      }
      ```
      通过将上述选项设置为 `true` 或 `false`，可动态控制按钮的显示，满足不同场景下的用户体验需求。例如，禁用 `erase` 可隐藏擦除功能。
  - **main.js**：Vue 应用入口，负责初始化 Vue 实例、注册插件（如 Vue Router、Vuex）以及全局配置。
  - **assets/**：存放静态资源，如图片、字体或 CSS 文件。
- **vue.config.js**：Vue CLI 配置文件，已配置将构建产物输出到 `frontend/dist/` 目录，并由 FastAPI 后端托管。
  - **代理配置**（开发模式）：支持将 `/api` 请求代理到 FastAPI 后端（默认 `http://localhost:8000`），避免跨域问题。
- **dist/**：前端编译后生成的静态文件（HTML、CSS、JS），由 `npm run build` 自动生成，供 FastAPI 后端直接提供。

### 📄 API 接口
所有后端接口定义在 `backend/app/routes/translation.py` 中，根路径为 `/api/translate`。
- **POST /api/translate/upload**：处理用户上传图片的翻译任务。
- **POST /api/translate/url**：处理基于 URL 的图片翻译任务。
- **POST /api/translate/save**：保存编辑器当前画布状态。
- **POST /api/translate/uploadExportedImage**：接收并保存前端导出的最终图片，建议定期清理。
- **GET /api/translate/result/{requestId}**：查询指定翻译任务的处理结果。
- **POST /api/translate/iopaint**：请求擦除服务，消耗一个积分。
- **POST /api/translate/uploadIoInpaintImage**：保存擦除操作的中间结果，建议定期清理。

## 🚀 运行指南

### 1️⃣ 先决条件
确保系统已安装以下软件：
- **Python 3.8+**：用于运行 FastAPI 后端。
- **Node.js 16.x+（含 npm）**：用于前端 Vue.js 开发与构建。
- **Git**（可选）：用于版本控制。

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
修改 backend/config.py，并填写 PicTech API 相关信息：
```dotenv
# .env 文件内容
PICOTECH_BASE_URL="http://example.com"
PICOTECH_API_KEY="你的AccountId"
PICOTECH_SECRET="你的SecretKey"

# 文件上传目录
UPLOAD_DIR="uploads"
```

- **PICOTECH_BASE_URL**：PicTech API 的基础 URL。
- **PICOTECH_API_KEY** 和 **PICOTECH_SECRET**：PicTech API 的凭证，用于调用图片处理服务。
- **UPLOAD_DIR**：用于存放用户上传的图片及程序生成的文件，项目启动时自动创建。

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
- 编译完成后，静态文件将生成在 `frontend/dist/` 目录。
- FastAPI 后端会自动从此目录提供静态资源，无需额外配置。

### 4️⃣ 启动应用
返回项目根目录，运行统一启动脚本：
```bash
cd ..
python run.py
```

启动成功后，控制台将显示类似以下日志：
```
INFO:     Started server process [12345]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 5️⃣ 访问应用
在浏览器中打开：
```
http://localhost:8000
```
您将看到 Vue.js 前端界面，所有 API 请求由 FastAPI 后端处理。可以通过上传图片、编辑、翻译等功能体验完整的图片翻译编辑器。

## 💡 开发模式提示
- **后端热重载**：`run.py` 已启用 Uvicorn 的热重载功能，修改后端代码后服务会自动重启。
- **前端热重载**：在 `frontend/` 目录下运行以下命令启动 Vue 开发服务器：
  ```bash
  npm run serve
  ```
  - 默认运行在 `http://localhost:8080`。
  - 为避免跨域问题，可在 `vue.config.js` 中配置代理，将 `/api` 请求转发到 FastAPI 后端：
    ```javascript
    module.exports = {
      devServer: {
        proxy: {
          '/api': {
            target: 'http://localhost:8000',
            changeOrigin: true
          }
        }
      }
    }
    ```

## 🤝 贡献
欢迎提交 Issue 或 Pull Request 来报告 Bug 或提出改进建议！请确保代码符合项目编码规范，并附上详细的描述。