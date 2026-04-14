from FastAPI import APIRouter,HTTPException,status
from schema.model_schema import RequestSchema,ResponseSchema

router = APIRouter(tags=["Predict"])

# @router.post("/predict")
# def predict_sentiment(request:RequestSchema) -> ResponseSchema:
#     # 3 Stages are required before Prediction
#     # Validate the input data -> Handled by Pydantic
#     # Preprocess the input data using vectorizer

