# backend/app/clients/pictech_api_client.py
import requests
import hmac
import hashlib
import base64
import time
import json
import logging
from typing import Dict, Any, Optional

from backend.app import config

# 日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PicTechApiClient:
    """
    PicTech API 客户端的 Python 实现。
    负责与远程 PicTech 服务通信，包括签名生成和HTTP请求。
    """

    def __init__(self):
        self.base_url = config.PICOTECH_BASE_URL
        self.api_key = config.PICOTECH_API_KEY
        self.secret_key = config.PICOTECH_SECRET
        self.session = requests.Session()

    def _generate_signature(self, params: Dict[str, str]) -> str:
        """生成 API 请求签名"""
        # 1. 过滤空值并按 key 排序
        sorted_items = sorted(
            [(k, v) for k, v in params.items() if v is not None and v != '']
        )

        # 2. 构造签名字符串
        param_string = "&".join(f"{k}={v}" for k, v in sorted_items)
        sign_string = f"{param_string}&SecretKey={self.secret_key}"
        logger.debug(f"用于签名的源字符串: {sign_string}")

        # 3. HMAC-SHA256 + Base64
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            sign_string.encode('utf-8'),
            hashlib.sha256
        ).digest()
        return base64.b64encode(signature).decode('utf-8')

    def _execute_post_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """执行 POST 请求的核心方法"""
        timestamp = str(int(time.time()))

        # 1. 添加公共参数
        payload["AccountId"] = self.api_key
        payload["Timestamp"] = timestamp

        # 2. 准备用于签名的参数 (所有值必须为字符串)
        params_for_signature = {k: str(v) for k, v in payload.items()}
        payload["Signature"] = self._generate_signature(params_for_signature)

        # 3. 发送请求
        full_url = self.base_url + endpoint
        headers = {"Content-Type": "application/json"}
        logger.info(f"发送请求到: {full_url}")
        logger.debug(f"请求体: {json.dumps(payload, indent=2)}")

        try:
            response = self.session.post(full_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()  # 如果状态码不是 2xx，则抛出异常
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"调用 PicTech API 失败: {e}")
            raise RuntimeError(f"调用 PicTech API 失败: {e}") from e

    # --- 图片翻译功能 ---
    def submit_translation_task_with_url(self, image_url: str, source_lang: str, target_lang: str) -> Dict[str, Any]:
        payload = {"ImageUrl": image_url, "SourceLanguage": source_lang, "TargetLanguage": target_lang}
        return self._execute_post_request("/submit_task", payload)

    def submit_translation_task_with_base64(self, image_base64: str, source_lang: str, target_lang: str) -> Dict[
        str, Any]:
        # 中文备注：根据Java代码，Base64字符串不应包含Data URL前缀
        if ',' in image_base64:
            image_base64 = image_base64.split(',', 1)[1]
        payload = {"ImageBase64": image_base64, "SourceLanguage": source_lang, "TargetLanguage": target_lang}
        return self._execute_post_request("/submit_task", payload)

    def query_translation_task_result(self, request_id: str) -> Dict[str, Any]:
        payload = {"RequestId": request_id}
        return self._execute_post_request("/query_result", payload)


# 单例模式，方便在应用中各处调用
pictech_client = PicTechApiClient()