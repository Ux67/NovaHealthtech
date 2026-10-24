"""
Nova Healthtech - Security Hardening & Rate-Limiting Middleware
Allows both localhost and local Wi-Fi / Mobile Hotspot IP connections.
"""

import html
import re
import time
from collections import defaultdict
from threading import Lock
from typing import Dict, List, Tuple
from flask import Request, Response


class SlidingWindowRateLimiter:
    def __init__(self) -> None:
        self.lock = Lock()
        self.requests: Dict[str, List[float]] = defaultdict(list)
        self.global_limit = 240
        self.strict_limit = 60
        self.window_seconds = 60.0

    def is_allowed(self, client_ip: str, is_strict_endpoint: bool = False) -> Tuple[bool, int]:
        now = time.time()
        max_allowed = self.strict_limit if is_strict_endpoint else self.global_limit
        key = f"{client_ip}:strict" if is_strict_endpoint else f"{client_ip}:global"

        with self.lock:
            cutoff = now - self.window_seconds
            self.requests[key] = [t for t in self.requests[key] if t > cutoff]
            current_count = len(self.requests[key])
            if current_count >= max_allowed:
                return False, 0
            self.requests[key].append(now)
            remaining = max_allowed - (current_count + 1)
            return True, remaining


rate_limiter = SlidingWindowRateLimiter()


def sanitize_input_text(raw_text: str, max_length: int = 500) -> str:
    if not raw_text:
        return ""
    truncated = str(raw_text).strip()[:max_length]
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", truncated)
    return html.escape(cleaned)


def apply_security_headers(response: Response) -> Response:
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=(self)"
    # Allow connect-src across local network / mobile hotspot IPs
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "connect-src 'self' *; "
        "frame-ancestors 'none';"
    )
    return response


def get_client_ip(req: Request) -> str:
    if req.headers.get("X-Forwarded-For"):
        return req.headers.get("X-Forwarded-For").split(",")[0].strip()
    return req.remote_addr or "127.0.0.1"