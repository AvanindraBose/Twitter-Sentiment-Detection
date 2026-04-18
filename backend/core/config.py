import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME = "IRIS SPECIES CLASSIFIER"

    API_KEY = os.environ["API_KEY"]
    JWT_ACCESS_SECRET_KEY = os.environ["JWT_ACCESS_SECRET_KEY"]
    JWT_REFRESH_SECRET_KEY = os.environ["JWT_REFRESH_SECRET_KEY"]

    JWT_ALGORITHM = "HS256"
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    MLFLOW_TRACKING_URI = os.environ["MLFLOW_TRACKING_URI"]
    MODEL_NAME = "IrisRandomForest"
    DATABASE_URL = os.environ["DATABASE_URL"]

settings = Settings()