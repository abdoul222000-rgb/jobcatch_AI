import hmac
import hashlib
import json
import base64
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .config import settings

def create_signed_session_cookie(data: dict) -> str:
    payload = json.dumps(data)
    encoded_payload = base64.urlsafe_b64encode(payload.encode()).decode()
    signature = hmac.new(settings.SECRET_KEY.encode(), encoded_payload.encode(), hashlib.sha256).hexdigest()
    return f"{encoded_payload}.{signature}"

def verify_signed_session_cookie(cookie_value: str):
    if not cookie_value or "." not in cookie_value:
        return None
    try:
        encoded_payload, signature = cookie_value.split(".", 1)
        expected_sig = hmac.new(settings.SECRET_KEY.encode(), encoded_payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            return None
        payload = base64.urlsafe_b64decode(encoded_payload.encode()).decode()
        return json.loads(payload)
    except Exception:
        return None

# Middleware des en-têtes de sécurité
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response
