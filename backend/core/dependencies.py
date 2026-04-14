import mlflow
import dagshub
import os
from mlflow.tracking import MlflowClient

mlflow.set_tracking_uri(os.getenv('MLFLOW_TRACKING_URI'))
dagshub.init(repo_owner='AvanindraBose', repo_name='Twitter-Sentiment-Detection', mlflow=True)
client = MlflowClient()

def load_model():
    model_name = "model"
    model_version = client.get_latest_versions(model_name, stages=["Production"])[0].version
    model_uri = f"models:/{model_name}/{model_version}"
    model = mlflow.pyfunc.load_model(model_uri)
    return model