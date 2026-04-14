from fastapi import APIRouter,HTTPException,status
from backend.schema.model_schema import RequestSchema,ResponseSchema
from backend.services.model_service import predict_sentiment

router = APIRouter(tags=["Predict"])

@router.get("/")
def root():
    return {"message": "Welcome to the Twitter Sentiment Detection API!"}

@router.post("/predict")
def prediction(request:RequestSchema) -> ResponseSchema:
    # 3 Stages are required before Prediction
    # Validate the input data -> Handled by Pydantic
    # Preprocess the input data using vectorizer
    # Make predictions using the loaded model
    try:
        data = {"text" : request.text}
        prediction = predict_sentiment(data)
        return {"sentiment": prediction['prediction']}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))



