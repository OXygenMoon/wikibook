# Wikibook OJ Secure Deployment

This project now has two very different deployment goals:

- Convenience: run everything together for demos or local verification.
- Security-first: isolate long-running services from the judge runtime.

For production, use the security-first layout below.

## Recommended topology

- `web`: serves HTTP traffic, does not mount `docker.sock`.
- `worker`: consumes judge tasks, talks to Docker through a restricted socket proxy.
- `dockerproxy`: exposes a reduced Docker API surface only to `worker`.
- `postgres`: internal-only database.
- `redis`: internal-only queue backend.
- `judge-runtime`: short-lived per-submission sandbox container.

## Why this is safer

- The public-facing `web` container cannot control the host Docker daemon.
- The `worker` container no longer mounts the raw Docker socket directly.
- `dockerproxy` only allows the Docker API sections needed by the judge flow.
- `web`, `worker`, and `bootstrap` run with read-only root filesystems, dropped Linux capabilities, `no-new-privileges`, and a small `/tmp` tmpfs.
- Python judge submissions are checked twice:
  - before enqueue in the Flask app
  - again inside the runtime sandbox

## What to avoid in production

- Do not use `run_local.sh` for internet-facing deployment.
- Do not mount `/var/run/docker.sock` into `web`.
- Do not use the all-in-one container layout when judge isolation matters more than convenience.
- Do not expose `postgres`, `redis`, or `dockerproxy` ports publicly.

## Recommended startup flow

1. Build the judge runtime image:

```bash
docker build -t wikibook-judge-runtime:latest -f judge_runtime/Dockerfile .
```

2. Start the isolated stack:

```bash
docker compose up -d postgres redis dockerproxy web worker
```

3. Initialize schema once:

```bash
docker compose --profile ops run --rm bootstrap
```

## Runtime notes

- `worker` connects to Docker through `tcp://dockerproxy:2375` by default.
- The runtime container still remains a separate short-lived container on purpose.
- If you want even stricter isolation later, the next step is moving the judge worker onto a dedicated host or VM.
