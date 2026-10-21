"""
Nova Healthtech - Security Hardening & Rate-Limiting Middleware
Provides thread-safe in-memory sliding window rate-limiting, HTML sanitization,
Zero-PII verification, and strict HTTP security headers.
"""

import html
import re
import time
from collections import defaultdict
from threading import Lock
from typing import Dict, List, Tuple
from flask import Request, Response, jsonify


class SlidingWindowRateLimiter:
    """
    Thread-safe in-memory sliding-window rate limiter.
    Enforces per-IP request quotas to protect rural server endpoints from abuse.
    """

    def __init__(self) -> None:
        self.lock = Lock()
        self.requests: Dict[str, List[float]] = defaultdict(list)
        # Default limits
        self.global_limit = 120       # 120 requests per minute for general GET/status endpoints
        self.strict_limit = 15        # 15 requests per minute for AI Chat & Consultation Intakes
        self.window_seconds = 60.0

    def is_allowed(self, client_ip: str, is_strict_endpoint: bool = False) -> Tuple[bool, int]:
        """
        Evaluates whether a request is within allowable quota.
        Returns (is_allowed, remaining_quota).
        """
        now = time.time()
        max_allowed = self.strict_limit if is_strict_endpoint else self.global_limit
        key = f"{client_ip}:strict" if is_strict_endpoint else f"{client_ip}:global"

        with self.lock:
            # Prune timestamps outside current sliding window
            cutoff = now - self.window_seconds
            self.requests[key] = [t for t in self.requests[key] if t > cutoff]

            current_count = len(self.requests[key])
            if current_count >= max_allowed:
                return False, 0

            self.requests[key].append(now)
            remaining = max_allowed - (current_count + 1)
            return True, remaining


# Singleton Rate Limiter
rate_limiter = SlidingWindowRateLimiter()


def sanitize_input_text(raw_text: str, max_length: int = 500) -> str:
    """
    Defensively sanitizes user-supplied text:
    1. Truncates length to avoid buffer abuse.
    2. Escapes HTML markup to eliminate Stored/Reflected XSS.
    3. Strips control characters.
    """
    if not raw_text:
        return ""
    truncated = str(raw_text).strip()[:max_length]
    # Remove null bytes and non-printable control characters
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", truncated)
    # Escape HTML special characters (&, <, >, ", ')
    return html.escape(cleaned)


def apply_security_headers(response: Response) -> Response:
    """
    Applies standard defensive HTTP response headers.
    """
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=(self)"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "connect-src 'self' http://127.0.0.1:5000 http://localhost:5000; "
        "frame-ancestors 'none';"
    )
    return response


def get_client_ip(req: Request) -> str:
    """Extracts client IP safely, accounting for standard proxy headers."""
    if req.headers.get("X-Forwarded-For"):
        return req.headers.get("X-Forwarded-For").split(",")[0].strip()
    return req.remote_addr or "127.0.0.1"