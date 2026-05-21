import os
import platform

from rq import SimpleWorker, Worker

from app import app
from queue_service import get_queue, get_redis_connection


def main():
    with app.app_context():
        connection = get_redis_connection()
        queue = get_queue(connection=connection)
        worker_mode = os.environ.get("JUDGE_WORKER_MODE", "").strip().lower()
        use_simple_worker = worker_mode == "simple" or (not worker_mode and platform.system() == "Darwin")
        worker_class = SimpleWorker if use_simple_worker else Worker
        worker = worker_class([queue], connection=connection)
        worker.work(with_scheduler=False)


if __name__ == "__main__":
    main()
