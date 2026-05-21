import os
import multiprocessing

bind = os.environ.get("GUNICORN_BIND", f"0.0.0.0:{os.environ.get('PORT', '5009')}")
workers = int(os.environ.get("GUNICORN_WORKERS", max(multiprocessing.cpu_count(), 2)))
worker_class = os.environ.get("GUNICORN_WORKER_CLASS", "sync")
worker_connections = int(os.environ.get("GUNICORN_WORKER_CONNECTIONS", "1000"))
max_requests = int(os.environ.get("GUNICORN_MAX_REQUESTS", "1000"))
max_requests_jitter = int(os.environ.get("GUNICORN_MAX_REQUESTS_JITTER", "50"))
preload_app = os.environ.get("GUNICORN_PRELOAD", "true").lower() == "true"

# Logging
accesslog = os.environ.get("GUNICORN_ACCESSLOG", "-")
errorlog = os.environ.get("GUNICORN_ERRORLOG", "-")
loglevel = os.environ.get("GUNICORN_LOGLEVEL", "info")

# Process naming
proc_name = os.environ.get("GUNICORN_PROC_NAME", "wikibook")

# Server mechanics
daemon = os.environ.get("GUNICORN_DAEMON", "false").lower() == "true"
pidfile = os.environ.get("GUNICORN_PIDFILE", "/tmp/wikibook.pid" if daemon else None)
user = None
group = None
tmp_upload_dir = None

# SSL
keyfile = None
certfile = None
