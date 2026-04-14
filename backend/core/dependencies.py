import mlflow
import dagshub
import os
import joblib
from mlflow.tracking import MlflowClient

mlflow.set_tracking_uri(os.getenv('MLFLOW_TRACKING_URI'))
dagshub.init(repo_owner='AvanindraBose', repo_name='Twitter-Sentiment-Detection', mlflow=True)
client = MlflowClient()

def load_artifacts() -> tuple:
    prod_model = client.get_latest_versions("model", stages=["Production"])[0]
    run_id = prod_model.run_id
    model_uri = f"models:/model/{prod_model.version}"

    model = mlflow.pyfunc.load_model(model_uri)

    vectorizer_uri = f"runs:/{run_id}/vectorizer.joblib"
    local_path = mlflow.artifacts.download_artifacts(vectorizer_uri)

    vectorizer = joblib.load(local_path)

    return (model, vectorizer)