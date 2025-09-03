# backend/app/clients/pictech_api_client.py

import requests
import hmac
import hashlib
import base64
import time
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

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
        self.BG_REMOVAL_SUBMIT_ENDPOINT = "/submit_remove_background_task"
        self.BG_REMOVAL_QUERY_ENDPOINT = "/query_remove_background_result"

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

    # --- 背景移除功能 ---
    def remove_background(self, image_path: Optional[str] = None, image_url: Optional[str] = None,
                          output_dir: str = "uploads", output_filename: str = "output.png") -> bool:
        """
        执行抠图任务的高级封装方法。
        自动完成提交、轮询查询、下载并保存结果图片的整个流程。

        Args:
            image_path (str, optional): 本地图片路径 (与 image_url 二选一)
            image_url (str, optional): 图片 URL (与 image_path 二选一)
            output_dir (str): 输出目录
            output_filename (str): 输出文件名

        Returns:
            bool: 是否成功完成整个流程
        """
        start_time = time.time()

        # --- 1. 准备请求参数 (Base64 或 URL) ---
        image_base64 = None
        if image_path:
            image_base64 = self._read_image_as_base64(image_path)
            if image_base64 is None:
                logger.error(f"从路径读取图片并转换为 Base64 失败: {image_path}")
                return False

        payload = {"BgColor": "white"}
        if image_base64:
            payload["ImageBase64"] = image_base64.split(',', 1)[1]  # 移除 Data URL 前缀
        elif image_url:
            payload["ImageUrl"] = image_url
        else:
            logger.error("必须提供本地图片路径(image_path)或图片URL(image_url)中的一个！")
            return False

        # --- 2. 提交抠图任务 ---
        logger.info("正在提交抠图任务...")
        try:
            submit_response = self._execute_post_request(self.BG_REMOVAL_SUBMIT_ENDPOINT, payload)
            if not submit_response or submit_response.get("Code", -1) != 200:
                error_message = submit_response.get("Message", "无响应") if submit_response else "无响应"
                logger.error(f"抠图任务提交失败: {error_message}")
                return False

            request_id = submit_response.get("RequestId")
            logger.info(f"任务提交成功, RequestId: {request_id}")
            logger.debug(f"提交任务响应详情: {json.dumps(submit_response, indent=2)}")
        except Exception as e:
            logger.error(f"提交抠图任务失败: {e}")
            return False

        # --- 3. 轮询查询结果 ---
        max_attempts = 15
        interval_ms = 1500

        for attempt in range(1, max_attempts + 1):
            try:
                result = self.query_remove_background_task_result(request_id)
                if not result:
                    logger.error(f"查询任务 {request_id} 失败: 无响应。")
                    return False

                logger.debug(f"查询响应 (第 {attempt} 次): {json.dumps(result, indent=2)}")
                code = result.get("Code", -1)

                if code == 200:  # 任务成功
                    data = result.get("Data")
                    if not data or "OutputUrl" not in data:
                        logger.error("任务成功，但响应中未找到有效的输出URL (OutputUrl)。")
                        return False

                    output_url = data["OutputUrl"]
                    logger.info(f"任务处理成功，结果图片URL: {output_url}")

                    # --- 4. 下载并保存图片 ---
                    try:
                        output_path = Path(output_dir) / output_filename
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        response = self.session.get(output_url, timeout=30)
                        response.raise_for_status()
                        with output_path.open("wb") as f:
                            f.write(response.content)
                        end_time = time.time()
                        duration = end_time - start_time
                        logger.info(f"图片已成功保存到: {output_path}")
                        logger.info(f"任务总耗时: {duration:.2f} 秒")
                        return True
                    except Exception as e:
                        logger.error(f"下载或保存图片失败: {e}")
                        return False
                elif code == 202:  # 任务处理中
                    logger.info(
                        f"任务 {request_id} 仍在处理中，{interval_ms / 1000.0}秒后重试 (尝试 {attempt}/{max_attempts})")
                    time.sleep(interval_ms / 1000.0)
                else:  # 任务失败
                    error_message = f"{result.get('Message', 'Unknown error')}, ErrorCode: {result.get('ErrorCode', 'N/A')}"
                    logger.error(f"任务 {request_id} 处理失败: {error_message}")
                    return False
            except Exception as e:
                logger.error(f"查询任务 {request_id} 失败: {e}")
                return False

        logger.error(f"任务 {request_id} 在 {max_attempts} 次尝试后仍未完成，已超时。")
        return False

    def query_remove_background_task_result(self, request_id: str) -> Dict[str, Any]:
        """
        查询指定任务 ID 的抠图结果。

        Args:
            request_id (str): 提交任务时获取的任务 ID

        Returns:
            Dict[str, Any]: API 返回的响应体
        """
        payload = {"RequestId": request_id}
        return self._execute_post_request(self.BG_REMOVAL_QUERY_ENDPOINT, payload)


# 单例模式
pictech_client = PicTechApiClient()
