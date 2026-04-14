from fastapi import FastAPI
from backend.api import routes_predict

app = FastAPI(title="Twitter Sentiment Detection API", description="API for detecting sentiment in tweets", version="1.0")

app.include_router(routes_predict.router , tags=["Predict"])
