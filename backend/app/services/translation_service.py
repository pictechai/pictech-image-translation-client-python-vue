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

    # --- 【新增】图像修复 (Inpainting) 相关服务 ---

    def iopaint(self, source_image_base64: str, mask_image_base64: str) -> str:
        """
        处理擦除逻辑，调用API客户端，保存结果文件，并返回新图片的Base64编码。
        """
        try:
            # 1. 调用API客户端执行AI服务，直接获取修复后的图片字节
            image_bytes = pictech_client.inpaint_image_sync(source_image_base64, mask_image_base64)

            # 2. 准备保存路径和文件名
            unique_image_name = str(uuid.uuid4())
            date_folder = datetime.now().strftime("%Y-%m-%d")

            # 中文备注：使用 Path 对象以更好地处理跨平台路径
            directory_path = Path(config.UPLOAD_DIR) / "iopaint" / date_folder
            directory_path.mkdir(parents=True, exist_ok=True)

            # 中文备注：假设返回的都是 png 格式
            new_image_name_with_ext = f"{unique_image_name}.png"
            file_path = directory_path / new_image_name_with_ext

            # 3. 将API返回的图片字节保存到文件 (用于调试或归档)
            with open(file_path, "wb") as f:
                f.write(image_bytes)
            logger.info(f"Inpainted image saved to: {file_path}")

            # 4. 将图片字节编码为 Base64 字符串，直接返回给前端，避免了文件再读取的IO操作
            new_image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            return new_image_base64

        except Exception as e:
            logger.error(f"[iopaint] 处理过程中发生错误: {e}", exc_info=True)
            raise RuntimeError(f"iopaint 处理失败: {e}") from e

    def upload_io_inpaint_image(self, image_base64: str) -> str:
        """
        接收 Inpaint 后的 Base64 图片，保存到项目静态资源目录并返回可访问 URL。
        """
        try:
            # 1. 解码 Base64
            image_bytes = base64.b64decode(image_base64)

            # 2. 确定保存路径
            save_path = "iopaint_front"
            date_folder = datetime.now().strftime("%Y-%m-%d")
            directory_path = Path(config.UPLOAD_DIR) / save_path / date_folder
            directory_path.mkdir(parents=True, exist_ok=True)

            # 3. 生成唯一文件名并保存
            unique_filename = f"{uuid.uuid4()}.png"
            physical_file_path = directory_path / unique_filename

            with open(physical_file_path, "wb") as f:
                f.write(image_bytes)

            # 4. 构造并返回前端可访问的 URL
            # 中文备注：URL路径分隔符应始终为 '/'
            final_url = f"/{save_path}/{date_folder}/{unique_filename}"
            logger.info(f"返回给前端的 URL: {final_url}")
            return final_url

        except base64.binascii.Error as e:
            logger.error(f"Base64 解码失败: {e}")
            raise ValueError("无效的Base64数据") from e
        except IOError as e:
            logger.error(f"文件写入或路径查找时发生IO异常: {e}")
            raise RuntimeError("文件保存失败，服务器IO错误") from e


# 单例
translation_service = TranslationService()
