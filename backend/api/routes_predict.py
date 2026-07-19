import time
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from backend.core.dependencies import get_current_user
from backend.core.rate_limiter import predict_rate_limiter
from backend.custom_metrics import (
    MODEL_INFERENCE_DURATION,
    PREDICTION_COUNTER,
    REQUEST_COUNT,
    REQUEST_DURATION,
    REQUEST_ERRORS,
    RESPONSE_LATENCY,
    RESPONSE_STATUS,
)
from backend.logging_fastapi.logger_api import prediction_logger
from backend.schema.model_schema import XquikBatchRequest, XquikBatchResponse, XquikPrediction
from backend.services.model_service import predict_sentiment

router = APIRouter(tags=["Predict"])
templates = Jinja2Templates(directory="backend/templates")


@router.post("/predict", response_class=HTMLResponse)
@RESPONSE_LATENCY.time()
async def prediction(
    request: Request,
    rate_limit_result: Annotated[str | None, Depends(predict_rate_limiter)],
    text: str = Form(...),
):
    endpoint = "/predict"
    method = request.method
    start_time = time.perf_counter()
    REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()

    try:
        user_id = get_current_user(request)

        if rate_limit_result == "rate_limited":
            REQUEST_ERRORS.labels(method=method, endpoint=endpoint, error_type="rate_limited").inc()
            RESPONSE_STATUS.labels(method=method, endpoint=endpoint, status_code="429").inc()
            return templates.TemplateResponse(
                request=request,
                name="dashboard.html",
                context={"error": "Experiencing heavy traffic. Kindly try again later."},
            )

        if rate_limit_result == "redis_unavailable":
            REQUEST_ERRORS.labels(method=method, endpoint=endpoint, error_type="redis_unavailable").inc()
            RESPONSE_STATUS.labels(method=method, endpoint=endpoint, status_code="503").inc()
            return templates.TemplateResponse(
                request=request,
                name="dashboard.html",
                context={"error": "Service temporarily unavailable. Please try again later."},
            )

    except HTTPException as e:
        prediction_logger.save_logs(
            f"Access validation failed while accessing prediction route: {e.detail}", log_level="warning"
        )

        refresh_token = request.cookies.get("refresh_token")

        if e.detail == "expired" and refresh_token:
            prediction_logger.save_logs("Access token expired. Redirecting to refresh endpoint.", log_level="info")
            RESPONSE_STATUS.labels(method=method, endpoint=endpoint, status_code="303").inc()
            return RedirectResponse(url="/auth/refresh?next=/dashboard", status_code=status.HTTP_303_SEE_OTHER)

        REQUEST_ERRORS.labels(method=method, endpoint=endpoint, error_type="auth_error").inc()
        RESPONSE_STATUS.labels(method=method, endpoint=endpoint, status_code="303").inc()
        return RedirectResponse(url="/auth/login?session=expired", status_code=status.HTTP_303_SEE_OTHER)

    try:
        prediction_logger.save_logs(f"Received prediction request from user: {user_id}", log_level="info")

        inference_start_time = time.perf_counter()

        result = await predict_sentiment({"text": text})

        MODEL_INFERENCE_DURATION.observe(time.perf_counter() - inference_start_time)

        prediction_logger.save_logs("Prediction made successfully", log_level="info")

        if result["prediction"] == 1:
            PREDICTION_COUNTER.labels(sentiment="happy").inc()
        else:
            PREDICTION_COUNTER.labels(sentiment="sad").inc()

        RESPONSE_STATUS.labels(method=method, endpoint=endpoint, status_code="200").inc()
        return templates.TemplateResponse(
            request=request, name="result.html", context={"sentiment": result["prediction"]}
        )

    except Exception as e:
        prediction_logger.save_logs(f"Error occurred while making prediction. Error: {str(e)}", log_level="error")
        REQUEST_ERRORS.labels(method=method, endpoint=endpoint, error_type=type(e).__name__).inc()
        RESPONSE_STATUS.labels(method=method, endpoint=endpoint, status_code="503").inc()
        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={"error": "Experiencing heavy traffic. Kindly try again later."},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    finally:
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(time.perf_counter() - start_time)


@router.post("/api/predict/xquik", response_model=XquikBatchResponse)
async def predict_xquik_batch(
    request: Request,
    payload: XquikBatchRequest,
    rate_limit_result: Annotated[str | None, Depends(predict_rate_limiter)],
):
    if rate_limit_result == "rate_limited":
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Experiencing heavy traffic. Kindly try again later."
        )

    if rate_limit_result == "redis_unavailable":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable. Please try again later.",
        )

    user_id = get_current_user(request)
    prediction_logger.save_logs(f"Received Xquik batch prediction request from user: {user_id}", log_level="info")

    predictions = []

    for index, row in enumerate(payload.tweets):
        text = row.readable_text()

        if not text:
            continue

        result = await predict_sentiment({"text": text})

        predictions.append(XquikPrediction(index=index, source_id=row.source_id(), sentiment=result["prediction"]))

    if not predictions:
        raise HTTPException(status_code=422, detail="No readable tweet text found in Xquik rows.")

    return XquikBatchResponse(predictions=predictions)
