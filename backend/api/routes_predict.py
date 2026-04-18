import logging
from fastapi import APIRouter,HTTPException,status,Request,Form
from backend.schema.model_schema import RequestSchema,ResponseSchema
from backend.services.model_service import predict_sentiment
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from backend.logging_fastapi.logger_api import prediction_logger

router = APIRouter(tags=["Predict"])
templates = Jinja2Templates(
    directory= "backend/templates"
)

@router.post("/predict",response_class=HTMLResponse)
def prediction(request:Request , text:str = Form(...)):
    # 3 Stages are required before Prediction
    # Validate the input data -> Handled by Pydantic
    # Preprocess the input data using vectorizer
    # Make predictions using the loaded model
    try:
        prediction_logger.save_logs(f"Received prediction request.", log_level='info')
        data = {"text" : text}
        result = predict_sentiment(data)
        prediction_logger.save_logs(f"Prediction made for request.", log_level='info')
        return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={"sentiment": result['prediction']}
    )
    except Exception as e:
        prediction_logger.save_logs(f"Error occurred while making prediction. Error: {str(e)}", log_level='error')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
