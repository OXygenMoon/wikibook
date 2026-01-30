import os

bind = "0.0.0.0:5009"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "wikibook"

# Server mechanics
daemon = True
pidfile = "/tmp/wikibook.pid"
user = None
group = None
tmp_upload_dir = None

# SSL
keyfile = None
certfile = None