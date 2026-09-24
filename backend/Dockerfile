FROM python:3.14-slim

WORKDIR /app

COPY requirements-serving.txt .

RUN python -m pip install \
    --no-cache-dir \
    -r requirements-serving.txt

COPY backend ./backend

COPY artifacts/final_model/model.joblib \
    ./artifacts/final_model/model.joblib

ENV MODEL_PATH=/app/artifacts/final_model/model.joblib

ENV PRODUCTION_LOG_PATH=/app/artifacts/production/inference_log.jsonl

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
