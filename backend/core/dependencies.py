import mlflow
import dagshub
import os
import joblib
from mlflow.tracking import MlflowClient
from backend.logging_fastapi.logger_api import prediction_logger,auth_logger
from fastapi import Header,HTTPException,status,Depends,Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.core.config import settings
from backend.core.security import verify_access_token , verify_refresh_token
from backend.core.database import AsyncSessionLocal
from typing import AsyncGenerator
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

load_dotenv()

try:
    mlflow.set_tracking_uri(os.getenv('MLFLOW_TRACKING_URI'))
    dagshub.init(repo_owner='AvanindraBose', repo_name='Twitter-Sentiment-Detection', mlflow=True)
    client = MlflowClient()
except Exception as e:
    prediction_logger.save_logs(f"Error occurred while initializing MLflow: {str(e)}", log_level="error")

_model,_vectorizer = None,None

def load_artifacts() -> tuple:
    global _model, _vectorizer
    if _model is not None and _vectorizer is not None:
        prediction_logger.save_logs("Model and vectorizer already loaded, using cached versions.", log_level="info")
        return (_model, _vectorizer)
    
    try:
        prod_model = client.get_latest_versions("model", stages=["Production"])[0]
        run_id = prod_model.run_id
        model_uri = f"models:/model/{prod_model.version}"

        _model = mlflow.pyfunc.load_model(model_uri)

        vectorizer_uri = f"runs:/{run_id}/vectorizer.joblib"
        local_path = mlflow.artifacts.download_artifacts(vectorizer_uri)

        _vectorizer = joblib.load(local_path)
        prediction_logger.save_logs("Model and vectorizer loaded successfully.", log_level="info")
    except Exception as e:
        prediction_logger.save_logs(f"Error occurred while loading artifacts: {str(e)}", log_level="error")
        raise e

    return (_model, _vectorizer)

REDIS_URL = os.getenv("REDIS_URL")
security = HTTPBearer()

def get_api_key(api_key:str = Header(...)):
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key"
        )

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            auth_logger.save_logs("Database session initialized successfully", log_level="info")
        except Exception as e:
            auth_logger.save_logs(f"Error occurred while initializing database session: {str(e)}", log_level="error")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection error"
            )
        finally:
            await session.close()
            auth_logger.save_logs("Database session closed", log_level="info")


# def get_current_user(
#         credentials:HTTPAuthorizationCredentials = Depends(security)
# ):
#     token = credentials.credentials
#     payload = verify_access_token(token)
#     if payload is None:
#         raise HTTPException(
#             status_code = status.HTTP_401_UNAUTHORIZED,
#             detail = "Invalid or expired access token"
#         )
    
#     return payload["sub"]

def get_current_user(
        request:Request
):
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        auth_logger.save_logs("Refresh Token Not Found In the Cookies",log_level="error")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not Authenticated"
        )

    payload = verify_refresh_token(refresh_token)
    if payload is None:
        auth_logger.save_logs("User ID Not Found in the Cookies",log_level="error")
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid or expired access token"
        )
    user_id = payload.get("sub")
    
    if not user_id : 

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session"
        )
    
    return user_id

# def get_redis_client() -> Redis:
#     try: 
#         auth_logger.save_logs("Attempting to connect to Redis", log_level="info")
#         return Redis.from_url(
#             REDIS_URL,
#             decode_responses=True,
#             socket_timeout=2,
#             socket_connect_timeout=2,
#         )
#     except Exception:
#         auth_logger.save_logs("Failed to connect to Redis", log_level="error")
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail="Service Temporarily Unavailable",
#         )


redis_client = None

def get_redis_client() -> Redis:
    global redis_client

    if redis_client:
        prediction_logger.save_logs("Using cached Redis client", log_level="info")
        return redis_client

    try:
        prediction_logger.save_logs(
            "Attempting to connect to Redis",
            log_level="info"
        )

        client = Redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_timeout=2,
            socket_connect_timeout=2,
        )

        client.ping()

        prediction_logger.save_logs(
            "Successfully connected to Redis",
            log_level="info"
        )

        redis_client = client
        return redis_client

    except Exception as e:
        prediction_logger.save_logs(
            f"Failed to connect to Redis | Error: {str(e)}",
            log_level="error"
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Temporarily Unavailable",
        )
    
def get_refresh_user_id(request: Request) -> str:
    # print("Cookies:", request.cookies) 
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        auth_logger.save_logs(
            "Refresh token missing in request cookies",
            log_level="warning"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    payload = verify_refresh_token(refresh_token)

    if not payload:
        auth_logger.save_logs(
            "Invalid refresh token received",
            log_level="warning"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    user_id = payload.get("sub")

    if not user_id:
        auth_logger.save_logs(
            "Refresh token payload missing user_id",
            log_level="warning"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    return user_id