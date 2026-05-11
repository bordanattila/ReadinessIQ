# ReadinessIQ

Logistics readiness API: inventory, shipments, maintenance, and supplier-style synthetic data surfaced through KPIs, site risk ranking, and part-level impact.

![Tests](https://github.com/bordanattila/ReadinessIQ/actions/workflows/test.yml/badge.svg)

## Quick start

1. **Environment** — Copy `.env.example` to `.env` and set `POSTGRES_*` / `DATABASE_URL` (see `docker-compose.yml` for variable names).

2. **Database** — From the repo root:

   ```bash
   docker compose up -d postgres
   ```

3. **Backend (local)** — Python 3.12+ recommended.

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r backend/requirements.txt
   ```

4. **Load data** — Generate CSVs under `data/raw/` (optional), then load into Postgres:

   ```bash
   python3 backend/scripts/generate_synthetic_data.py
   python3 backend/scripts/load_csv_to_postgres.py
   ```

5. **Run API** — From `backend/`:

   ```bash
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   Open **http://localhost:8000/docs** for Swagger.

**Docker backend** — `docker compose up -d --build` starts Postgres + API (see `docker-compose.yml`). Rebuild the backend image after code changes.

## Tests

From the repo root (uses `pytest.ini`):

```bash
pytest
```

## Layout (high level)

```
ReadinessIQ/
├── backend/app/          # FastAPI app and routers
├── backend/scripts/      # Synthetic data + CSV loader
├── backend/tests/
├── data/raw/             # Generated CSVs (gitignored patterns may apply)
├── docker-compose.yml
└── backend/Dockerfile
```
