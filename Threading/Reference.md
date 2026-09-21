# Modern Python Stack — Reference & Interview Prep

## The stack at a glance

| Layer | Tool | The one thing to know |
|---|---|---|
| Runtime | CPython 3.13 | Cooperative concurrency; GIL still standard |
| Packaging | uv + `pyproject.toml` | The lockfile is the contract |
| Isolation | venv + direnv | One interpreter per project |
| Quality | ruff | Format and lint are separate commands |
| Concurrency | asyncio | Blocking calls stall everything |
| Web | FastAPI + Pydantic | Types are runtime validation |
| Data | async SQLAlchemy + asyncpg | Lazy loading doesn't work here |
| Schema | Alembic | Migrations meet non-empty tables |
| Tests | pytest + pytest-asyncio | Needs a mode and a loop |
| Ship | Docker multi-stage | Build deps stay out of runtime |
| Run | Kubernetes + Helm | Tags move, digests don't |
| Automate | GitHub Actions | Permissions are deny-by-default |

## Layer notes

### Packaging
- `pyproject.toml` holds dependencies and tool config in one file.
- `uv lock` resolves; `uv sync --frozen` installs exactly that and fails if stale.
- Apps run from source via `PYTHONPATH`; libraries get installed.
- **Gotcha:** a package can break you at import time, not call time.

### Environment
- One venv per project; direnv auto-activates on `cd`.
- Config comes from env vars, loaded from a gitignored `.env`.
- **Gotcha:** env vars with hardcoded defaults fail silently into production values.

### Code quality
- `ruff format` and `ruff check` are two separate commands.
- Pin the version — a minor bump reformats everything.
- **Gotcha:** `check` does not verify formatting.

### asyncio
- One thread, one event loop; tasks yield at `await`.
- `gather` / `TaskGroup` for concurrency; `Semaphore` to bound fan-out.
- Blocking work goes to `asyncio.to_thread`.
- **Gotcha:** `CancelledError` is a `BaseException` — `except Exception` never sees it.

### Web layer
- FastAPI + Pydantic v2 — type annotations are runtime validation.
- `response_model` filters output; `Depends` for dependency injection.
- **Gotcha:** a blocking call inside `async def` stalls every request on that worker.

### Data layer
- Async SQLAlchemy + asyncpg, one session per request.
- Eager-load relationships with `selectinload` / `joinedload`.
- pgvector turns Postgres into a vector store.
- **Gotcha:** `MissingGreenlet` means lazy I/O happened where none was allowed.

### Migrations
- Alembic with chained revisions; expand–contract for safe changes.
- Autogenerate produces a draft, not a finished migration.
- **Gotcha:** `NOT NULL` without a default dies on non-empty tables.

### Testing
- pytest + pytest-asyncio; fixtures scoped via `conftest.py`.
- Mock at the boundary; use a real containerized DB for SQL.
- Per-test timeouts so one hang doesn't eat the run.
- **Gotcha:** a test that passes before and after the fix asserts nothing.

### Containers
- Multi-stage Docker: build the venv, copy it into a clean slim image.
- Dependency layers before source layers, for caching.
- **Gotcha:** tags move — identify images by digest.

### Kubernetes
- Deployment (long-lived) / Job (one-shot) / CronJob (scheduled).
- Readiness gates traffic; liveness restarts.
- Requests reserve and schedule; limits cap and OOM-kill.
- **Gotcha:** `IfNotPresent` with a moving tag can rerun old cached bytes.

### CI/CD
- Change gating, reusable workflows, OIDC instead of long-lived keys.
- Cache on the lockfile hash.
- **Gotcha:** "skipped" looks green but isn't "passed."
- **Gotcha:** declaring `permissions:` sets every unlisted scope to none.

---

# Interview Exercise — Practice Checklist

**Total: ~60 minutes**

## Part A · 30 min · no AI — thread-safe in-memory message queue

Requirements:

- [ ] FIFO ordering per topic
- [ ] Message TTL
- [ ] At-least-once delivery with a visibility timeout
- [ ] Ack semantics (redelivery if not acked in time)

What interviewers look for:

- [ ] Per-topic locks rather than one global lock
- [ ] Lazy TTL expiry with an eager fallback
- [ ] Visibility timeout implementing at-least-once delivery
- [ ] Monotonic clock (`time.monotonic()`) for TTL, not wall clock
- [ ] Ack semantics with redelivery on timeout (a story for consumer death)

## Part B · 25 min · AI allowed — expose it as an MCP server

Use the official Python SDK, with four tools:

- [ ] `publish_message`
- [ ] `consume_message`
- [ ] `ack_message`
- [ ] `queue_size`

What interviewers look for:

- [ ] Tool descriptions written for an LLM caller — not docstrings copied off the queue methods
- [ ] Structured errors
- [ ] Explicit schemas

## Part C · 5 min — discussion

Be ready to talk through:

- [ ] What breaks at 10k msg/sec
- [ ] Persistence strategy
- [ ] Multi-LLM-client semantics

## Red flags to avoid

- A single global lock
- TTL ignored on consume
- No story for what happens when a consumer dies
- `signal.alarm` for timeouts
