# backend/app/routers/translate.py
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Path as FastApiPath
from fastapi.responses import JSONResponse
from ..services.translation_service import translation_service
from ..models.translation_models import UrlTranslationRequest, Base64TranslationRequest, UploadedImageRequest, \
    IopaintRequest, UploadIoInpaintImageRequest
import uuid
import logging
import traceback  # 引入 traceback 模块以打印详细的异常堆栈
from typing import Dict, Any

# 中文备注：APIRouter 类似于 Spring 的 @RequestMapping 在类上的作用
router = APIRouter(
    prefix="/api/translate",
    tags=["Translation"]  # 用于API文档分组
)


# --- 【新增】辅助方法，用于创建标准响应体 (类似Java中的实现) ---
def create_success_response(url: str) -> Dict[str, Any]:
    return {
        "Code": 200,
        "Message": "上传成功",
        "Data": {"Url": url}
    }


def create_error_response(error_message: str, code: int = 500) -> Dict[str, Any]:
    return {
        "Code": code,
        "Message": error_message,
        "Data": None
    }


@router.post("/url")
async def submit_from_url(request: UrlTranslationRequest):
    try:
        result = translation_service.submit_task_from_url(
            request.imageUrl, request.sourceLanguage, request.targetLanguage
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/base64")
async def submit_from_base64(request: Base64TranslationRequest):
    try:
        result = translation_service.submit_task_from_base64(
            request.imageBase64, request.sourceLanguage, request.targetLanguage
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def submit_from_file_upload(
        file: UploadFile = File(...),
        sourceLanguage: str = Form(...),
        targetLanguage: str = Form(...)
):
    if not file:
        raise HTTPException(status_code=400, detail="上传文件不能为空")
    try:
        result = await translation_service.submit_task_from_file(file, sourceLanguage, targetLanguage)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/result/{request_id}")
async def query_result(request_id: str = FastApiPath(..., title="任务ID")):
    try:
        result = translation_service.query_task_result(request_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 获取 logger 实例
import logging  # 新增：导入 logging 模块

logger = logging.getLogger(__name__)  # 新增：定义 logger 实例


@router.post("/uploadExportedImage")
async def upload_exported_image(request: UploadedImageRequest):
    try:
        accessible_path = translation_service.save_exported_image(
            request.imageBase64,
            request.filename
        )
        # --- 日志点 4: 构建响应之前 ---
        response_content = {
            "message": "文件上传成功",
            "filePath": accessible_path
        }
        logger.info(f"准备返回 200 OK 响应, 内容: {response_content}")

        # 正常返回
        return JSONResponse(status_code=200, content=response_content)

    except ValueError as e:
        # 捕获由 service 层主动抛出的已知错误 (例如 Base64 解码失败)
        logger.error(f"请求处理失败 (ValueError): {e}")
        # 打印完整的 traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=400, detail=f"请求无效: {e}")

    except Exception as e:
        # --- 关键日志点 5: 捕获所有其他未知异常 ---
        # 这里是定位 500 错误的关键
        logger.critical("!!!!!!!!!! /uploadExportedImage 发生严重异常 !!!!!!!!!!")
        logger.critical(f"异常类型: {type(e).__name__}")
        logger.critical(f"异常信息: {e}")
        # 使用 traceback 打印完整的异常调用堆栈，这会告诉我们错误发生在哪一行代码
        logger.critical("异常 Traceback:\n" + traceback.format_exc())
        logger.critical("================== /uploadExportedImage - 请求异常结束 ==================")

        # 抛出标准的 500 错误，FastAPI 会处理它
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {e}")


# save 接口可以根据需要实现，这里先提供一个模拟的
@router.post("/save")
async def save_state():
    return {
        "Code": 200,
        "Message": "状态保存成功 (Python后端模拟)",
        "RequestId": str(uuid.uuid4())
    }


# --- 【新增接口】---

@router.post("/iopaint", summary="代理图像擦除 (Inpainting) 请求")
async def perform_inpainting(request: IopaintRequest):
    """
    这个接口接收前端的擦除请求，然后由后端调用Python的IOPaint服务，
    从而绕过浏览器的跨域限制。
    """
    try:
        new_image_base64 = translation_service.iopaint(request.image, request.mask)
        # 5. 将新的 Base64 字符串返回给前端
        return JSONResponse(
            status_code=200,
            content={"newImageBase64": new_image_base64}
        )
    except Exception as e:
        logger.error(f"Inpainting process failed: {e}", exc_info=True)
        # 记录详细错误日志
        return JSONResponse(
            status_code=500,
            content={"error": f"图像擦除处理失败: {e}"}
        )


@router.post("/uploadIoInpaintImage", summary="保存 Inpaint 后的图片并返回 URL")
async def upload_io_inpaint_image(request: UploadIoInpaintImageRequest):
    """
    【重构接口】接收 Inpaint 后的 Base64 图片，保存到项目静态资源目录并返回可访问 URL
    """
    # 1. 参数校验 (由 Pydantic 自动完成，如果 imageData 为空会报错)
    image_base64 = request.imageData
    if not image_base64:
        return JSONResponse(
            status_code=400,
            content=create_error_response("图片数据(imageData)不能为空", code=400)
        )

    try:
        final_url = translation_service.upload_io_inpaint_image(image_base64)
        # 6. 返回标准格式的成功响应
        return JSONResponse(
            status_code=200,
            content=create_success_response(final_url)
        )
    except ValueError as e:
        # 中文备注：捕获由 service 层主动抛出的已知错误 (例如 Base64 解码失败)
        logger.error(f"Base64 解码失败: {e}")
        return JSONResponse(
            status_code=400,
            content=create_error_response(f"无效的Base64数据: {e}", code=400)
        )
    except Exception as e:
        logger.error(f"文件保存时发生未知异常: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=create_error_response(f"文件保存失败，服务器内部错误: {e}")
        )
