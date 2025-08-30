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
        # 【新增】API 端点常量
        self.INPAINT_SYNC_ENDPOINT = "/inpaint_image_sync"
        self.TRANSLATION_SUBMIT_ENDPOINT = "/submit_task"
        self.TRANSLATION_QUERY_ENDPOINT = "/query_result"

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
        """执行 POST 请求的核心方法 (返回 JSON)"""
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
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"调用 PicTech API (JSON) 失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"错误响应体: {e.response.text}")
            raise RuntimeError(f"调用 PicTech API 失败: {e}") from e

    # 【新增】执行 POST 请求的核心方法，专门用于期望返回二进制数据 (如图片) 的场景
    def _execute_post_request_for_bytes(self, endpoint: str, payload: Dict[str, Any]) -> bytes:
        """执行 POST 请求并返回原始字节流"""
        timestamp = str(int(time.time()))

        # 1. 添加公共参数
        payload["AccountId"] = self.api_key
        payload["Timestamp"] = timestamp

        # 2. 准备签名
        params_for_signature = {k: str(v) for k, v in payload.items()}
        payload["Signature"] = self._generate_signature(params_for_signature)

        # 3. 设置 HTTP Header
        headers = {
            "Content-Type": "application/json",
            "Accept": "*/*"  # 中文备注：告诉服务器客户端可以接受任何类型的响应
        }

        full_url = self.base_url + endpoint
        logger.info(f"发送请求到: {full_url} (期望返回 bytes)")
        logger.debug(f"请求体: {json.dumps(payload, indent=2)}")

        try:
            response = self.session.post(full_url, json=payload, headers=headers, timeout=60)  # 修复超时可能更长
            response.raise_for_status()
            # 检查响应头，如果返回的是json错误信息，则解析并抛出
            if 'application/json' in response.headers.get('Content-Type', ''):
                error_data = response.json()
                error_message = error_data.get("Message", "Unknown API error")
                logger.error(f"API 返回了 JSON 格式的错误: {error_message}")
                raise RuntimeError(f"API Error: {error_message}")

            return response.content
        except requests.exceptions.RequestException as e:
            logger.error(f"调用 PicTech API (Bytes) 失败: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"错误响应体: {e.response.text}")
            raise RuntimeError(f"调用 PicTech API 失败: {e}") from e

    # --- 图片翻译功能 ---
    def submit_translation_task_with_url(self, image_url: str, source_lang: str, target_lang: str) -> Dict[str, Any]:
        payload = {"ImageUrl": image_url, "SourceLanguage": source_lang, "TargetLanguage": target_lang}
        return self._execute_post_request(self.TRANSLATION_SUBMIT_ENDPOINT, payload)

    def submit_translation_task_with_base64(self, image_base64: str, source_lang: str, target_lang: str) -> Dict[
        str, Any]:
        if ',' in image_base64:
            image_base64 = image_base64.split(',', 1)[1]
        payload = {"ImageBase64": image_base64, "SourceLanguage": source_lang, "TargetLanguage": target_lang}
        return self._execute_post_request(self.TRANSLATION_SUBMIT_ENDPOINT, payload)

    def query_translation_task_result(self, request_id: str) -> Dict[str, Any]:
        payload = {"RequestId": request_id}
        return self._execute_post_request(self.TRANSLATION_QUERY_ENDPOINT, payload)

    # --- 【新增】图片修复 (Inpainting) 功能 ---
    def inpaint_image_sync(self, source_image_base64: str, mask_image_base64: str) -> bytes:
        """
        执行同步图片修复任务，并返回修复后的图片字节流。
        """
        logger.info("正在启动同步图片修复任务...")

        # 中文备注：根据服务端要求，传递不带 "data:" 前缀的纯 Base64 字符串
        if ',' in source_image_base64:
            source_image_base64 = source_image_base64.split(',', 1)[1]
        if ',' in mask_image_base64:
            mask_image_base64 = mask_image_base64.split(',', 1)[1]

        payload = {
            "image": source_image_base64,
            "mask": mask_image_base64
        }

        image_bytes = self._execute_post_request_for_bytes(self.INPAINT_SYNC_ENDPOINT, payload)
        if not image_bytes:
            logger.error("API调用失败或未返回有效的图片数据。")
            raise RuntimeError("API did not return valid image data.")

        return image_bytes


# 单例模式
pictech_client = PicTechApiClient()