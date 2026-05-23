import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _as_bool(name, default=False):
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _as_int(name, default):
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default


def normalize_database_url(database_url):
    if not database_url:
        return "postgresql+psycopg://wikibook:wikibook@127.0.0.1:5432/wikibook"
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql://", 1)
    return database_url


def configure_app(app):
    database_url = normalize_database_url(
        os.environ.get("DATABASE_URL", "postgresql+psycopg://wikibook:wikibook@127.0.0.1:5432/wikibook")
    )
    is_sqlite = database_url.startswith("sqlite")

    engine_options = {
        "pool_pre_ping": True,
    }
    if not is_sqlite:
        engine_options.update(
            {
                "pool_size": _as_int("SQLALCHEMY_POOL_SIZE", 10),
                "max_overflow": _as_int("SQLALCHEMY_MAX_OVERFLOW", 20),
                "pool_recycle": _as_int("SQLALCHEMY_POOL_RECYCLE", 1800),
            }
        )

    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret"),
        APP_LOG_FILE=os.environ.get("APP_LOG_FILE", ""),
        DEBUG_TRACEBACK_TO_CLIENT=_as_bool("DEBUG_TRACEBACK_TO_CLIENT", False),
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS=engine_options,
        SQLALCHEMY_ECHO=_as_bool("SQLALCHEMY_ECHO", False),
        UPLOAD_FOLDER=os.path.join(app.root_path, "static/uploads"),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,
        PERMANENT_SESSION_LIFETIME=timedelta(days=30),
        REDIS_URL=os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0"),
        RQ_DEFAULT_TIMEOUT=_as_int("RQ_DEFAULT_TIMEOUT", 600),
        JUDGE_QUEUE_NAME=os.environ.get("JUDGE_QUEUE_NAME", "judge"),
        JUDGE_RUNTIME_IMAGE=os.environ.get("JUDGE_RUNTIME_IMAGE", "wikibook-judge-runtime:latest"),
        JUDGE_DOCKER_HOST=os.environ.get("JUDGE_DOCKER_HOST", ""),
        JUDGE_DEFAULT_TIME_LIMIT_MS=_as_int("JUDGE_DEFAULT_TIME_LIMIT_MS", 2000),
        JUDGE_DEFAULT_MEMORY_LIMIT_MB=_as_int("JUDGE_DEFAULT_MEMORY_LIMIT_MB", 256),
        JUDGE_CONTAINER_CPUS=float(os.environ.get("JUDGE_CONTAINER_CPUS", "1.0")),
        JUDGE_CONTAINER_PIDS_LIMIT=_as_int("JUDGE_CONTAINER_PIDS_LIMIT", 128),
        JUDGE_ALLOW_NETWORK=_as_bool("JUDGE_ALLOW_NETWORK", False),
        JUDGE_MAX_OUTPUT_BYTES=_as_int("JUDGE_MAX_OUTPUT_BYTES", 65536),
        JUDGE_RESULT_TTL_SECONDS=_as_int("JUDGE_RESULT_TTL_SECONDS", 604800),
        DB_RENDER_AS_BATCH=is_sqlite,
        AUTO_INIT_DB=_as_bool("AUTO_INIT_DB", False),
    )
