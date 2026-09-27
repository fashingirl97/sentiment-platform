"""认证与安全：基于 HMAC 签名的轻量 Token（无额外密码学依赖）。"""
import base64
import hashlib
import hmac
import json
import time

# 生产环境应通过环境变量覆盖，此处提供默认值
SECRET_KEY = "sentiment-platform-demo-secret-2026"
TOKEN_TTL = 60 * 60 * 12  # Token 有效期 12 小时


def hash_password(password: str) -> str:
    """使用 PBKDF2 对密码做单向哈希。"""
    salt = b"sentiment-salt"
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return base64.b64encode(dk).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return hmac.compare_digest(hash_password(password), hashed)


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64url_decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def create_token(user_id: int, username: str, role: str) -> str:
    """生成携带用户信息的签名 Token。"""
    header = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64url_encode(
        json.dumps({"sub": user_id, "username": username, "role": role, "exp": time.time() + TOKEN_TTL}).encode()
    )
    signing_input = f"{header}.{payload}".encode()
    signature = _b64url_encode(hmac.new(SECRET_KEY.encode(), signing_input, hashlib.sha256).digest())
    return f"{header}.{payload}.{signature}"


def decode_token(token: str) -> dict | None:
    """校验并解析 Token，非法或过期返回 None。"""
    try:
        header, payload, signature = token.split(".")
        signing_input = f"{header}.{payload}".encode()
        expected = _b64url_encode(hmac.new(SECRET_KEY.encode(), signing_input, hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            return None
        data = json.loads(_b64url_decode(payload))
        if data.get("exp", 0) < time.time():
            return None
        return data
    except Exception:
        return None
