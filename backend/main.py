import logging
from fastapi import FastAPI
from backend.api import routes_predict,routes_auth,routes_health
from backend.core.database import engine,Base
from backend.middlewares.response_logger import ResponseLoggerMiddleware
from fastapi.staticfiles import StaticFiles
from src.logger_class import CustomLogger , create_log_path
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Shutdown
    await engine.dispose()

app = FastAPI(title="Twitter Sentiment Detection API", description="API for detecting sentiment in tweets", version="1.0")
app.add_middleware(ResponseLoggerMiddleware)

log_path = create_log_path("prediction")

prediction_logger = CustomLogger(
    logger_name="prediction",
    log_filename=log_path
)

prediction_logger.set_log_level(logging.INFO)

prediction_logger.save_logs("Prediction system started", log_level="info")

app.mount("/static", StaticFiles(directory="backend/static"), name="static")
app.include_router(routes_predict.router , tags=["Predict"])
