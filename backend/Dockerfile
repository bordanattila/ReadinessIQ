FROM python:3.12-slim

WORKDIR /app

# Install deps first (better layer caching)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Layout mirrors `backend/` locally: `app` and `utils` are sibling packages.
# `from utils.connect_to_db` only works if both exist here and PYTHONPATH
# includes /app (same rule as running `uvicorn` from the `backend/` directory).
COPY backend/app ./app
COPY backend/utils ./utils

ENV PYTHONPATH=/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
