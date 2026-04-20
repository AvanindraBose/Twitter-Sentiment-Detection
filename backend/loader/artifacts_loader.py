import mlflow
import joblib
import dagshub
from mlflow.tracking import MlflowClient
from backend.logging_fastapi.logger_api import prediction_logger
from backend.core.config import settings

try:
    mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
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
