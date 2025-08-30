# backend/app/models/translation_models.py
from pydantic import BaseModel, Field
from typing import Optional, Any


# 中文备注：Pydantic 模型用于定义API请求和响应的数据结构，并提供自动校验

class UrlTranslationRequest(BaseModel):
    imageUrl: str = Field(..., alias='imageUrl')
    sourceLanguage: str
    targetLanguage: str


class Base64TranslationRequest(BaseModel):
    imageBase64: str
    sourceLanguage: str
    targetLanguage: str


class UploadedImageRequest(BaseModel):
    requestId: Optional[str] = None
    filename: Optional[str] = "exported.png"
    imageBase64: str


# --- 【新增】Inpainting 接口模型 ---
class IopaintRequest(BaseModel):
    # 中文备注：字段名与Java代码保持一致
    image: str = Field(..., description="源图的 Base64 编码")
    mask: str = Field(..., description="蒙版图的 Base64 编码")


class UploadIoInpaintImageRequest(BaseModel):
    # 中文备注：字段名与Java代码保持一致
    imageData: str = Field(..., description="修复后图片的 Base64 编码")
