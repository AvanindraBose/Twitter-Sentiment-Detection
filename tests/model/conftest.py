import mlflow
import os
import joblib
import pytest
import pandas as pd
from mlflow.tracking import MlflowClient
from pathlib import Path


@pytest.fixture(scope="session")
def mlflow_connector() -> MlflowClient:
    dagshub_token = os.getenv("DAGSHUB_PAT")

    if not dagshub_token:
        pytest.skip("DAGSHUB_PAT not set")

    os.environ["MLFLOW_TRACKING_USERNAME"] = dagshub_token
    os.environ["MLFLOW_TRACKING_PASSWORD"] = dagshub_token

    mlflow.set_tracking_uri(
        "https://dagshub.com/AvanindraBose/Twitter-Sentiment-Detection.mlflow"
    )

    return MlflowClient()


@pytest.fixture(scope="session")
def prod_model_version(mlflow_connector: MlflowClient):
    versions = mlflow_connector.get_latest_versions("model", stages=["Production"])

    if not versions:
        pytest.skip("No production model found")

    return versions[0]


@pytest.fixture(scope="session")
def model_uri(prod_model_version) -> str:
    return f"models:/model/{prod_model_version.version}"


@pytest.fixture(scope="session")
def vectorizer_uri(prod_model_version) -> str:
    return f"runs:/{prod_model_version.run_id}/vectorizer.joblib"


@pytest.fixture(scope="session")
def trained_model(model_uri: str):
    return mlflow.pyfunc.load_model(model_uri=model_uri)


@pytest.fixture(scope="session")
def vectorizer(vectorizer_uri: str):
    local_path = mlflow.artifacts.download_artifacts(vectorizer_uri)
    return joblib.load(local_path)

@pytest.fixture(scope="session")
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def processed_test_data_path(repo_root: Path) -> Path:
    return repo_root / "data" / "processed" / "test_bow.csv"


@pytest.fixture(scope="session")
def processed_test_df(processed_test_data_path: Path) -> pd.DataFrame:
    return pd.read_csv(processed_test_data_path)


@pytest.fixture(scope="session")
def processed_test_features(processed_test_df: pd.DataFrame) -> pd.DataFrame:
    return processed_test_df.iloc[:, :-1]


@pytest.fixture(scope="session")
def processed_test_target(processed_test_df: pd.DataFrame):
    return processed_test_df.iloc[:, -1]


@pytest.fixture(scope="session")
def holdout_data(processed_test_df: pd.DataFrame) -> pd.DataFrame:
    return processed_test_df


@pytest.fixture(scope="session")
def sample_input_text() -> str:
    return "hi how are you"
