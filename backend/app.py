import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import joblib
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)


MODEL_PATH = Path(
    os.getenv(
        "MODEL_PATH",
        "artifacts/final_model/model.joblib",
    )
)

INFERENCE_LOG_PATH = Path(
    os.getenv(
        "INFERENCE_LOG_PATH",
        "artifacts/production/inference_log.jsonl",
    )
)

FEEDBACK_LOG_PATH = Path(
    os.getenv(
        "FEEDBACK_LOG_PATH",
        "artifacts/production/feedback_log.jsonl",
    )
)

FRONTEND_ORIGIN = os.getenv(
    "FRONTEND_ORIGIN",
    "http://localhost:5173",
)


logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s "
        "%(levelname)s "
        "%(name)s "
        "%(message)s"
    ),
)

logger = logging.getLogger(
    "customer-support-inference"
)


# ---------------------------------------------------------------------------
# Prometheus metrics
# ---------------------------------------------------------------------------

PREDICTIONS_TOTAL = Counter(
    "inference_predictions_total",
    "Total number of successful model predictions.",
)

PREDICTIONS_BY_INTENT = Counter(
    "inference_predictions_by_intent_total",
    "Total predictions grouped by predicted intent.",
    ["intent"],
)

INFERENCE_ERRORS_TOTAL = Counter(
    "inference_errors_total",
    "Total number of failed inference requests.",
)

INFERENCE_LATENCY_SECONDS = Histogram(
    "inference_request_duration_seconds",
    "Time spent performing model inference.",
)

FEEDBACK_TOTAL = Counter(
    "inference_feedback_total",
    "Total user feedback events.",
    ["verdict"],
)

CORRECTIONS_TOTAL = Counter(
    "inference_corrections_total",
    "Corrections grouped by predicted and corrected intent.",
    [
        "predicted_intent",
        "corrected_intent",
    ],
)


model = None


# ---------------------------------------------------------------------------
# API schemas
# ---------------------------------------------------------------------------

class PredictionRequest(BaseModel):
    text: str = Field(
        min_length=1,
        max_length=5000,
    )


class PredictionResponse(BaseModel):
    request_id: str
    intent: str


class FeedbackRequest(BaseModel):
    request_id: str

    verdict: Literal[
        "correct",
        "incorrect",
    ]

    text: str | None = Field(
        default=None,
        max_length=5000,
    )

    predicted_intent: str

    corrected_intent: str | None = None


class FeedbackResponse(BaseModel):
    status: str


# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------

def append_jsonl(
    path: Path,
    record: dict,
):
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "a",
        encoding="utf-8",
    ) as file:
        file.write(
            json.dumps(
                record,
                ensure_ascii=False,
            )
            + "\n"
        )


def log_inference(
    *,
    request_id: str,
    text: str,
    predicted_intent: str,
    duration_seconds: float,
):
    record = {
        "request_id": request_id,
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        "message_length_chars": len(text),
        "word_count": len(
            text.split()
        ),
        "predicted_intent":
            predicted_intent,
        "duration_seconds":
            duration_seconds,
    }

    append_jsonl(
        INFERENCE_LOG_PATH,
        record,
    )


def log_feedback(
    feedback: FeedbackRequest,
):
    record = {
        "request_id":
            feedback.request_id,
        "timestamp":
            datetime.now(
                timezone.utc
            ).isoformat(),
        "verdict":
            feedback.verdict,
        "predicted_intent":
            feedback.predicted_intent,
        "corrected_intent":
            feedback.corrected_intent,
    }

    # Raw text is stored only for explicitly submitted
    # incorrect-prediction feedback so it can later be
    # reviewed and labeled for retraining.
    if (
        feedback.verdict == "incorrect"
        and feedback.text
    ):
        record["text"] = feedback.text

    append_jsonl(
        FEEDBACK_LOG_PATH,
        record,
    )


# ---------------------------------------------------------------------------
# Application lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model

    if not MODEL_PATH.exists():
        raise RuntimeError(
            f"Model file does not exist: "
            f"{MODEL_PATH}"
        )

    logger.info(
        "Loading model from %s",
        MODEL_PATH,
    )

    model = joblib.load(
        MODEL_PATH
    )

    logger.info(
        "Model loaded successfully."
    )

    yield


app = FastAPI(
    title=(
        "Customer Support Intent Classifier"
    ),
    description=(
        "Production inference API with "
        "monitoring and feedback collection."
    ),
    version="3.0.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_ORIGIN,
    ],
    allow_credentials=False,
    allow_methods=[
        "GET",
        "POST",
    ],
    allow_headers=[
        "*",
    ],
)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded":
            model is not None,
        "model_path":
            str(MODEL_PATH),
    }


@app.get("/metrics")
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.post(
    "/predict",
    response_model=PredictionResponse,
)
def predict(
    request: PredictionRequest,
):
    request_id = str(
        uuid.uuid4()
    )

    start_time = (
        time.perf_counter()
    )

    try:
        prediction = model.predict(
            [request.text]
        )

        predicted_intent = str(
            prediction[0]
        )

        duration = (
            time.perf_counter()
            - start_time
        )

        PREDICTIONS_TOTAL.inc()

        PREDICTIONS_BY_INTENT.labels(
            intent=predicted_intent
        ).inc()

        INFERENCE_LATENCY_SECONDS.observe(
            duration
        )

        log_inference(
            request_id=request_id,
            text=request.text,
            predicted_intent=
                predicted_intent,
            duration_seconds=
                duration,
        )

        logger.info(
            "prediction request_id=%s "
            "intent=%s latency=%.6f",
            request_id,
            predicted_intent,
            duration,
        )

        return {
            "request_id":
                request_id,
            "intent":
                predicted_intent,
        }

    except Exception:
        INFERENCE_ERRORS_TOTAL.inc()

        logger.exception(
            "Inference failed "
            "request_id=%s",
            request_id,
        )

        raise


@app.post(
    "/feedback",
    response_model=FeedbackResponse,
)
def feedback(
    request: FeedbackRequest,
):
    if (
        request.verdict == "incorrect"
        and not request.corrected_intent
    ):
        return {
            "status":
                "correction_required"
        }

    FEEDBACK_TOTAL.labels(
        verdict=request.verdict
    ).inc()

    if (
        request.verdict == "incorrect"
        and request.corrected_intent
    ):
        CORRECTIONS_TOTAL.labels(
            predicted_intent=
                request.predicted_intent,
            corrected_intent=
                request.corrected_intent,
        ).inc()

    log_feedback(
        request
    )

    logger.info(
        "feedback request_id=%s "
        "verdict=%s "
        "predicted=%s corrected=%s",
        request.request_id,
        request.verdict,
        request.predicted_intent,
        request.corrected_intent,
    )

    return {
        "status": "recorded"
    }
