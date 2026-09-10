"""rrweb 全局异常处理（对齐爬虫 FastAPI 写法）。"""

import logging
import traceback

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

log = logging.getLogger("rrweb")


async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTPException：统一返回 msg（管理端拦截器只读 msg）。"""
    content = {
        "msg": None,
    }
    detail = exc.detail
    if isinstance(detail, dict):
        content.update(detail)
    else:
        content["msg"] = str(detail)
    return JSONResponse(status_code=exc.status_code, content=content)


async def exception_handler(request: Request, exc: Exception):
    """未捕获异常：记日志并返回统一结构。"""
    err_detail = traceback.format_exc()
    log.error(f"exception_handler: {err_detail}")
    return JSONResponse(
        status_code=500,
        content={
            "msg": "服务异常，请稍后重试",
        },
    )
