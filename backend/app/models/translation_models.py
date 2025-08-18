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

# 更多模型可以根据需要从Java DTO迁移...