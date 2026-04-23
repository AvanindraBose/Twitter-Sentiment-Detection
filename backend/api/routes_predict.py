from fastapi import APIRouter, HTTPException, status, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from backend.logging_fastapi.logger_api import prediction_logger
from backend.core.dependencies import get_current_user
from backend.services.model_service import predict_sentiment

router = APIRouter(tags=["Predict"])
templates = Jinja2Templates(directory="backend/templates")

@router.post("/predict", response_class=HTMLResponse)
async def prediction(request: Request, text: str = Form(...)):
    try:
        user_id = get_current_user(request)

    except HTTPException as e:
        prediction_logger.save_logs(
            f"Access validation failed while accessing prediction route: {e.detail}",
            log_level="warning"
        )

        refresh_token = request.cookies.get("refresh_token")
        print(refresh_token)

        if e.detail == "expired" and refresh_token:
            prediction_logger.save_logs(
                "Access token expired. Redirecting to refresh endpoint.",
                log_level="info"
            )
            return RedirectResponse(
                url="/auth/refresh?next=/",
                status_code=status.HTTP_303_SEE_OTHER
            )

        return RedirectResponse(
            url="/auth/login",
            status_code=status.HTTP_303_SEE_OTHER
        )

    try:
        prediction_logger.save_logs(
            f"Received prediction request from user: {user_id}",
            log_level="info"
        )

        result = await predict_sentiment({"text": text})

        prediction_logger.save_logs(
            "Prediction made successfully",
            log_level="info"
        )

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
        # raise HTTPException(
        #     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #     detail=str(e)
        # )
        return templates.TemplateResponse(
            request=request,
            name = "index.html",
            context = {"error": "Experiencing heavy traffic. Kindly try again later." }
        )