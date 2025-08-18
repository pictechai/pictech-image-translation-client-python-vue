# backend/app/config.py
import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# PicTech API 配置
# 中文备注：建议将敏感信息（如KEY）存储在 .env 文件中，而不是直接写在代码里
# 在 backend 目录下创建一个 .env 文件，内容如下：
# PICOTECH_BASE_URL="http://your.api.base.url"
# PICOTECH_API_KEY="your_api_key"
# PICOTECH_SECRET="your_secret"
PICOTECH_BASE_URL = os.getenv("PICOTECH_BASE_URL", "http://example.com")
PICOTECH_API_KEY = os.getenv("PICOTECH_API_KEY", "aaaa")
PICOTECH_SECRET = os.getenv("PICOTECH_SECRET", "bbbbb")

# 文件上传配置
# 中文备注：路径相对于项目根目录的 backend 文件夹
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")