# Wikibook Platform Upgrade

This project is now prepared for a `PostgreSQL + Redis + Docker Judge Worker` deployment model.

## What Changed

- `DATABASE_URL` now supports PostgreSQL cleanly through SQLAlchemy/psycopg.
- Redis-backed RQ queue support was added for asynchronous judge execution.
- Judge infrastructure was added:
  - `JudgeTask`
  - `JudgeTaskResult`
  - `judge_worker.py`
  - Dockerized judge runtime under `judge_runtime/`
- Request-time auto schema mutation was removed.
- Platform/bootstrap tasks are now explicit CLI commands.
- Fresh schema bootstrap now stamps the database to the current Alembic head.

## New Operational Commands

Initialize platform data only:

```bash
flask --app app wikibook init-platform
```

Create schema, run compatibility upgrades, and seed baseline data:

```bash
flask --app app wikibook init-platform --with-schema
```

Queue an existing judge task:

```bash
flask --app app wikibook enqueue-judge-task 1
```

## Recommended Docker Compose Flow

1. Copy environment template:

```bash
cp .env.example .env
```

2. Build the app and judge runtime images:

```bash
docker compose build web worker
docker compose --profile build build judge-runtime
```

3. Start PostgreSQL and Redis:

```bash
docker compose up -d postgres redis
```

4. Bootstrap schema and seed data:

```bash
docker compose --profile ops run --rm bootstrap
```

5. Start web and worker:

```bash
docker compose up -d web worker
```

## Judge Runtime Notes

- The current runtime supports `python`, `c`, and `cpp`.
- The worker launches the runtime container through the Docker socket.
- Network access is disabled by default for judged code.
- Results are stored in `judge_task` and `judge_task_result`.

## Existing SQLite Deployments

For existing SQLite instances, use this rollout order:

1. Back up the SQLite file first.
2. Bring up PostgreSQL.
3. Run `flask --app app wikibook init-platform --with-schema` against PostgreSQL.
4. Migrate data from SQLite into PostgreSQL with your preferred tool.

Recommended tooling:

- `pgloader` for direct SQLite to PostgreSQL migration
- or a one-time ETL script if you want field-by-field cleanup during migration

## Important Behavioral Change

The app no longer calls `db.create_all()` or schema patching on first request.

That behavior was intentionally removed so that:

- web processes stay stateless
- worker processes do not race on schema changes
- PostgreSQL deployments behave predictably
- migrations become explicit operational steps

## Migration History Note

The legacy Alembic history in this repository was not originally authored as a full empty-database bootstrap chain.

Because of that, the recommended path for a brand-new environment is:

1. `flask --app app wikibook init-platform --with-schema`
2. let that command stamp the DB to the current migration head
3. use normal Alembic migrations for future incremental changes
