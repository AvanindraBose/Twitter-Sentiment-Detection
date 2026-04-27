import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME = "IRIS SPECIES CLASSIFIER"

    API_KEY = os.getenv("API_KEY")
    JWT_ACCESS_SECRET_KEY = os.getenv("JWT_ACCESS_SECRET_KEY")
    JWT_REFRESH_SECRET_KEY = os.getenv("JWT_REFRESH_SECRET_KEY")

    JWT_ALGORITHM = "HS256"
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI")
    MODEL_NAME = "IrisRandomForest"
    DATABASE_URL = os.getenv("DATABASE_URL")

settings = Settings()