import os
from fastapi import APIRouter,HTTPException,status,Request,Form
from backend.schema.model_schema import RequestSchema,ResponseSchema
from backend.services.model_service import predict_sentiment
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Predict"])
templates = Jinja2Templates(
    directory= "backend/templates"
)

@router.get("/",response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse(request = request , name = "index.html")

@router.post("/predict",response_class=HTMLResponse)
def prediction(request:Request , text:str = Form(...)):
    # 3 Stages are required before Prediction
    # Validate the input data -> Handled by Pydantic
    # Preprocess the input data using vectorizer
    # Make predictions using the loaded model
    try:
        data = {"text" : text}
        result = predict_sentiment(data)
        return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={"sentiment": result['prediction']}
    )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
