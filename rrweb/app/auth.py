"""
rrweb 接口认证：转发 token 至主站 /api/up/auth/verify/，与 YaoCaiUserAuth 校验逻辑一致。
成功结果短时缓存，避免同 token 连续请求重复打主站。
"""

import asyncio
import time
from typing import Any, Optional

import httpx
from fastapi import Header, HTTPException, status

from config import AUTH_VERIFY_CACHE_TTL, AUTH_VERIFY_TIMEOUT, AUTH_VERIFY_URL

# token -> (expire_at_monotonic, auth_data)
_verify_cache: dict[str, tuple[float, dict[str, Any]]] = {}
_verify_cache_lock = asyncio.Lock()

# 复用连接池的异步客户端，随应用生命周期创建与关闭
_verify_client: Optional[httpx.AsyncClient] = None
_verify_client_lock = asyncio.Lock()


async def get_verify_client() -> httpx.AsyncClient:
    """获取（必要时懒创建）主站鉴权请求用的异步客户端。"""
    global _verify_client
    if _verify_client is None or _verify_client.is_closed:
        async with _verify_client_lock:
            if _verify_client is None or _verify_client.is_closed:
                _verify_client = httpx.AsyncClient(timeout=AUTH_VERIFY_TIMEOUT)
    return _verify_client


async def close_verify_client() -> None:
    """关闭鉴权客户端，供应用关闭时释放连接。"""
    global _verify_client
    if _verify_client is not None and not _verify_client.is_closed:
        await _verify_client.aclose()
    _verify_client = None


def _extract_raw_token(
    token: Optional[str] = None,
    authorization: Optional[str] = None,
) -> Optional[str]:
    """从 token 头或 Authorization: JWT xxx 取出原始 token 字符串。"""
    raw = token or authorization
    if not raw or not isinstance(raw, str):
        return None
    raw = raw.strip()
    if raw.upper().startswith("JWT "):
        raw = raw[4:].strip()
    return raw or None


async def _get_cached_auth(raw_token: str) -> Optional[dict[str, Any]]:
    """读取未过期的 verify 缓存；过期则删除并返回 None。"""
    now = time.monotonic()
    async with _verify_cache_lock:
        item = _verify_cache.get(raw_token)
        if item is None:
            return None
        expire_at, data = item
        if expire_at <= now:
            _verify_cache.pop(raw_token, None)
            return None
        return data


async def _set_cached_auth(raw_token: str, data: dict[str, Any]) -> None:
    """写入 verify 成功结果缓存。"""
    if AUTH_VERIFY_CACHE_TTL <= 0:
        return
    expire_at = time.monotonic() + AUTH_VERIFY_CACHE_TTL
    async with _verify_cache_lock:
        _verify_cache[raw_token] = (expire_at, data)
        # 简单限长，防止异常流量撑爆内存
        if len(_verify_cache) > 4096:
            oldest_key = min(_verify_cache, key=lambda k: _verify_cache[k][0])
            _verify_cache.pop(oldest_key, None)


async def require_auth(
    token: Optional[str] = Header(None, alias="token"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> dict:
    """
    FastAPI 依赖：将 token 转发主站 verify 接口校验。
    未配置 AUTH_VERIFY_URL、缺 token、主站返回非成功均视为未授权。
    校验成功结果按 AUTH_VERIFY_CACHE_TTL 秒缓存。
    """
    if not AUTH_VERIFY_URL:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务未配置 AUTH_VERIFY_URL（config.py）",
        )

    raw_token = _extract_raw_token(token=token, authorization=authorization)
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或缺少 token",
        )

    cached = await _get_cached_auth(raw_token)
    if cached is not None:
        return cached

    client = await get_verify_client()
    try:
        resp = await client.get(
            AUTH_VERIFY_URL,
            headers={
                "token": raw_token,
                "Authorization": f"JWT {raw_token}",
            },
        )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="无法连接鉴权服务",
        ) from exc

    if resp.status_code == 401:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或登录已失效",
        )
    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="鉴权服务不可用",
        )

    try:
        body = resp.json()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="鉴权服务响应异常",
        ) from exc

    if body.get("code") != 100 or not body.get("data", {}).get("valid"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=body.get("msg") or "未登录或登录已失效",
        )

    auth_data = body["data"]
    await _set_cached_auth(raw_token, auth_data)
    return auth_data
