FROM python:3.12-slim

WORKDIR /app

COPY site_simulator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY site_simulator//app ./app

ENV PYTHONPATH=/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9000"]