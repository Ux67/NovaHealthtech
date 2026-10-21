"""
Nova Healthtech - Production Gunicorn Configuration
Configures multi-threaded WSGI workers, dynamic port binding,
and extended timeouts for generative AI assistant queries.
"""

import os

# Dynamic Port Binding: Respects $PORT on cloud platforms (Render, AWS, Heroku)
port = os.getenv("PORT", "5000")
bind = f"0.0.0.0:{port}"

# Worker Configuration
# Use gthread workers: perfect for I/O-bound workloads (Gemini API calls, SQLite queries)
workers = int(os.getenv("WEB_CONCURRENCY", "2"))
threads = int(os.getenv("GUNICORN_THREADS", "4"))
worker_class = "gthread"

# Concurrency & Timeout
# Allow up to 120s for slow AI completions or rural high-latency edge requests
timeout = 120
keepalive = 5

# Security & Limits
max_requests = 1000            # Automatically restart workers after 1000 requests to prevent memory leaks
max_requests_jitter = 50       # Jitter prevents all workers from restarting simultaneously
limit_request_line = 4094
limit_request_fields = 100

# Logging: Stream to standard output and error for CloudWatch, Render Logs, or Datadog
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" (%(D)s µs)'

# Process Naming
proc_name = "nova_healthtech_wsgi"

# Do not preload app to ensure SQLite file locks and thread pools initialize per worker
preload_app = False