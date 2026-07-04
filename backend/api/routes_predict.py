import time
from fastapi import APIRouter, HTTPException, status, Request, Form , Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from backend.logging_fastapi.logger_api import prediction_logger
from backend.core.dependencies import get_current_user
from backend.services.model_service import predict_sentiment
from backend.core.rate_limiter import predict_rate_limiter
from backend.custom_metrics import (
    PREDICTION_COUNTER,
    MODEL_INFERENCE_DURATION,
    REQUEST_COUNT,
    RESPONSE_LATENCY,
    RESPONSE_STATUS,
    REQUEST_DURATION,
    REQUEST_ERRORS
)

router = APIRouter(tags=["Predict"])
templates = Jinja2Templates(directory="backend/templates")

@router.post("/predict", response_class=HTMLResponse)
@RESPONSE_LATENCY.time()
async def prediction(request: Request, text: str = Form(...) , _ = Depends(predict_rate_limiter)):
    endpoint = "/predict"
    method = request.method
    start_time = time.perf_counter()
    REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()

    try:
        user_id = get_current_user(request)

        if _ == "rate_limited" :
            REQUEST_ERRORS.labels(method=method, endpoint=endpoint, error_type="rate_limited").inc()
            RESPONSE_STATUS.labels(method=method, endpoint=endpoint, status_code="429").inc()
            return templates.TemplateResponse(
            request=request,
            name = "dashboard.html",
            context = {"error": "Experiencing heavy traffic. Kindly try again later." }
        )

        if _ == "redis_unavailable":
            REQUEST_ERRORS.labels(method=method, endpoint=endpoint, error_type="redis_unavailable").inc()
            RESPONSE_STATUS.labels(method=method, endpoint=endpoint, status_code="503").inc()
            return templates.TemplateResponse(
                    request=request,
                    name="dashboard.html",
                    context={"error": "Service temporarily unavailable. Please try again later."}
                )

    except HTTPException as e:
        prediction_logger.save_logs(
            f"Access validation failed while accessing prediction route: {e.detail}",
            log_level="warning"
        )

        refresh_token = request.cookies.get("refresh_token")

        if e.detail == "expired" and refresh_token:
            prediction_logger.save_logs(
                "Access token expired. Redirecting to refresh endpoint.",
                log_level="info"
            )
            RESPONSE_STATUS.labels(method=method, endpoint=endpoint, status_code="303").inc()
            return RedirectResponse(
                url="/auth/refresh?next=/dashboard",
                status_code=status.HTTP_303_SEE_OTHER
            )

        REQUEST_ERRORS.labels(method=method, endpoint=endpoint, error_type="auth_error").inc()
        RESPONSE_STATUS.labels(method=method, endpoint=endpoint, status_code="303").inc()
        return RedirectResponse(
            url="/auth/login?session=expired",
            status_code=status.HTTP_303_SEE_OTHER
        )

    try:
        prediction_logger.save_logs(
            f"Received prediction request from user: {user_id}",
            log_level="info"
        )

        inference_start_time = time.perf_counter()

        result = await predict_sentiment({"text": text})

        MODEL_INFERENCE_DURATION.observe(time.perf_counter() - inference_start_time)

        prediction_logger.save_logs(
            "Prediction made successfully",
            log_level="info"
        )

        if result["prediction"] == 1 :
            PREDICTION_COUNTER.labels(sentiment = "happy").inc()
        else:
            PREDICTION_COUNTER.labels(sentiment="sad").inc()

        RESPONSE_STATUS.labels(method=method, endpoint=endpoint, status_code="200").inc()
        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={"sentiment": result["prediction"]}
        )
    
    except Exception as e:
        prediction_logger.save_logs(
            f"Error occurred while making prediction. Error: {str(e)}",
            log_level="error"
        )
        REQUEST_ERRORS.labels(method=method, endpoint=endpoint, error_type=type(e).__name__).inc()
        RESPONSE_STATUS.labels(method=method, endpoint=endpoint, status_code="503").inc()
        return templates.TemplateResponse(
            request=request,
            name = "dashboard.html",
            context = {"error": "Experiencing heavy traffic. Kindly try again later." },
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE 
        )
    finally:
        REQUEST_DURATION.labels(method=method,endpoint=endpoint).observe(time.perf_counter() - start_time)
