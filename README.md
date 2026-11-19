# Hearback

Hearback tracks job applications automatically. You log applications on the web app
(and later with a Chrome extension); Hearback reads your Gmail (read-only) to detect
rejections, online assessments, interviews and offers, then updates each application's
status and color. It also parses your resume into editable fields.

I'm building it for my own Summer 2027 internship search.

## Status

Phase 1 (foundation) in progress: FastAPI + PostgreSQL backend, Next.js web app,
manual application tracker, resume upload and parsing, AWS infrastructure in Terraform.

## Repo layout

| Folder      | What's in it                        |
| ----------- | ----------------------------------- |
| `apps/api`  | FastAPI backend (Python)            |
| `apps/web`  | Next.js web app (TypeScript)        |
| `infra`     | Terraform for AWS                   |

## Run locally

Requires Docker Desktop.

```bash
docker compose up --build        # database + migrations + API
curl localhost:8000/health       # {"status":"ok"}
```

- API: http://localhost:8000 (interactive docs at http://localhost:8000/docs)
- Code in `apps/api/app/` reloads automatically when you save.
- `docker compose down` stops everything; `docker compose down -v` also deletes the database.

### Run the tests

Requires [uv](https://docs.astral.sh/uv/) and the database container running.

```bash
docker compose up -d db
cd apps/api
uv run pytest -q
```

## Design

See the Phase 1 design doc: https://docs.google.com/document/d/1HYYPfwelRg9yJr_nn5DDzfhxa5qFovhIThFm9gwEOOc/edit?usp=sharing
