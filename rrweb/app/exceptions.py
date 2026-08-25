"""rrweb 全局异常处理（对齐爬虫 FastAPI 写法）。"""

import logging
import traceback

from fastapi import Request
from fastapi.responses import JSONResponse

log = logging.getLogger("rrweb")


async def exception_handler(request: Request, exc: Exception):
    """
    未捕获异常：记日志并返回统一结构。
    主动 raise 的 HTTPException 仍由 FastAPI 默认处理（原状态码 + detail）。
    """
    err_detail = traceback.format_exc()
    log.error(f"exception_handler: {err_detail}")
    return JSONResponse(
        status_code=500,
        content={
            "msg": "服务异常，请稍后重试",
            "detail": err_detail,
        },
    )
