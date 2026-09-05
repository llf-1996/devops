"""
rrweb 接口认证：转发 token 至主站 /api/up/auth/verify/，与 YaoCaiUserAuth 校验逻辑一致。
"""

from typing import Optional

import requests
from fastapi import Header, HTTPException, status

from config import AUTH_VERIFY_TIMEOUT, AUTH_VERIFY_URL


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


def require_auth(
    token: Optional[str] = Header(None, alias="token"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> dict:
    """
    FastAPI 依赖：将 token 转发主站 verify 接口校验。
    未配置 AUTH_VERIFY_URL、缺 token、主站返回非成功均视为未授权。
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

    try:
        resp = requests.get(
            AUTH_VERIFY_URL,
            headers={
                "token": raw_token,
                "Authorization": f"JWT {raw_token}",
            },
            timeout=AUTH_VERIFY_TIMEOUT,
        )
    except requests.RequestException as exc:
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

    return body["data"]
