from flask import current_app
from redis import Redis
from rq import Queue


def get_redis_connection(redis_url=None):
    return Redis.from_url(redis_url or current_app.config["REDIS_URL"])


def get_queue(name=None, connection=None):
    queue_name = name or current_app.config["JUDGE_QUEUE_NAME"]
    queue_connection = connection or get_redis_connection()
    return Queue(queue_name, connection=queue_connection, default_timeout=current_app.config["RQ_DEFAULT_TIMEOUT"])


def enqueue_judge_task(task_id):
    queue = get_queue()
    job = queue.enqueue("judge_tasks.process_judge_task", task_id, job_timeout=current_app.config["RQ_DEFAULT_TIMEOUT"])
    return job
