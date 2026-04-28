import mlflow
import joblib
import os
from dotenv import load_dotenv
from mlflow.tracking import MlflowClient
from backend.logging_fastapi.logger_api import prediction_logger
from backend.core.config import settings
from fastapi.concurrency import run_in_threadpool

load_dotenv()
# Facing Performance Issues hence using Async loader functions

try:
    dagshub_token = os.getenv("DAGSHUB_PAT")

    if not dagshub_token:
        prediction_logger.save_logs("Dagshub Token not found in env file",log_level='warning')
        os.environ["MLFLOW_TRACKING_USERNAME"] = dagshub_token
        os.environ["MLFLOW_TRACKING_PASSWORD"] = dagshub_token

    mlflow.set_tracking_uri(
        "https://dagshub.com/AvanindraBose/Twitter-Sentiment-Detection.mlflow"
    )
    client = MlflowClient()
except Exception as e:
    prediction_logger.save_logs(f"Error occurred while initializing MLflow: {str(e)}", log_level="error")

_model,_vectorizer = None,None

# joblib.load(local_path) , client.get_latest_versions("model", stages=["Production"])[0] -> These are not awaitable functions

async def load_artifacts() -> tuple:
    global _model, _vectorizer
    if _model is not None and _vectorizer is not None:
        prediction_logger.save_logs("Model and vectorizer already loaded, using cached versions.", log_level="info")
        return (_model, _vectorizer)
    
    try:
        prod_model = client.get_latest_versions("model", stages=["Production"])[0]
        run_id = prod_model.run_id
        model_uri = f"models:/model/{prod_model.version}"

        _model = await run_in_threadpool(
            mlflow.pyfunc.load_model,
            model_uri
        )

        vectorizer_uri = f"runs:/{run_id}/vectorizer.joblib"
        local_path = await run_in_threadpool (mlflow.artifacts.download_artifacts,vectorizer_uri)

        _vectorizer = await run_in_threadpool(
            joblib.load,
            local_path
        )
        prediction_logger.save_logs("Model and vectorizer loaded successfully.", log_level="info")
    except Exception as e:
        prediction_logger.save_logs(f"Error occurred while loading artifacts: {str(e)}", log_level="error")
        raise e

    return (_model, _vectorizer)
