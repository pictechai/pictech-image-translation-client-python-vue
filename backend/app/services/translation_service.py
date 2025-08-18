# backend/app/services/translation_service.py
import base64
import os
import uuid
from datetime import datetime
from fastapi import UploadFile

from backend.app.clients.pictech_api_client import pictech_client
from .. import config
import logging  # 新增：导入 logging 模块

logger = logging.getLogger(__name__)  # 新增：定义 logger 实例


class TranslationService:
    def submit_task_from_url(self, image_url: str, source_lang: str, target_lang: str):
        return pictech_client.submit_translation_task_with_url(image_url, source_lang, target_lang)

    def submit_task_from_base64(self, image_base64: str, source_lang: str, target_lang: str):
        return pictech_client.submit_translation_task_with_base64(image_base64, source_lang, target_lang)

    async def submit_task_from_file(self, file: UploadFile, source_lang: str, target_lang: str):
        # 异步读取文件内容
        contents = await file.read()
        # 将文件内容编码为 Base64
        base64_data = base64.b64encode(contents).decode('utf-8')
        # 加上 Data URL 前缀（如果需要）或直接发送
        # 这里我们直接发送原始 base64 数据
        return pictech_client.submit_translation_task_with_base64(base64_data, source_lang, target_lang)

    def query_task_result(self, request_id: str):
        return pictech_client.query_translation_task_result(request_id)

    def save_exported_image(self, image_base64: str, filename: str) -> str:
        """保存前端导出的Base64图片，并返回可访问路径"""
        try:
            image_bytes = base64.b64decode(image_base64)

            date_folder = datetime.now().strftime("%Y-%m-%d")
            # 中文备注：确保上传目录存在
            directory_path = os.path.join(config.UPLOAD_DIR, date_folder)
            os.makedirs(directory_path, exist_ok=True)

            # 生成唯一文件名
            file_extension = os.path.splitext(filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(directory_path, unique_filename)

            with open(file_path, "wb") as f:
                f.write(image_bytes)

            # 返回前端可访问的相对路径
            accessible_path = f"/{date_folder}/{unique_filename}"
            logger.info(f"成功保存导出图片，访问路径: {accessible_path}")
            return accessible_path

        except (base64.binascii.Error, IOError) as e:
            logger.error(f"保存导出图片失败: {e}")
            raise ValueError(f"保存图片失败: {e}") from e


# 单例
translation_service = TranslationService()
