import mlflow
import os
import logging
import json
from datetime import datetime, timezone
from src.logger_class import CustomLogger, create_log_path
from pathlib import Path
from mlflow.tracking import MlflowClient
from dotenv import load_dotenv


load_dotenv()
# mlflow configurations
# mlflow.set_tracking_uri(os.getenv('MLFLOW_TRACKING_URI'))
# dagshub.init(repo_owner='AvanindraBose', repo_name='Twitter-Sentiment-Detection', mlflow=True)

dagshub_token = os.getenv("DAGSHUB_PAT")
if not dagshub_token:
    raise EnvironmentError("DAGSHUB_PAT environment variable is not set")

os.environ["MLFLOW_TRACKING_USERNAME"] = dagshub_token
os.environ["MLFLOW_TRACKING_PASSWORD"] = dagshub_token

dagshub_url = "https://dagshub.com"
repo_owner = "AvanindraBose"
repo_name = "Twitter-Sentiment-Detection"

# Set up MLflow tracking URI
mlflow.set_tracking_uri(f'{dagshub_url}/{repo_owner}/{repo_name}.mlflow')

client = MlflowClient()

# logging configuration
logger = logging.getLogger('model_evaluation')
logger.setLevel('DEBUG')

console_handler = logging.StreamHandler()
console_handler.setLevel('DEBUG')

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)


logger.addHandler(console_handler)

# File Handler Configuration
log_file_path = create_log_path("Model Registry")
registry_logger = CustomLogger(
    logger_name="Registry",
    log_filename=log_file_path
)

registry_logger.set_log_level(level=logging.INFO)

registry_logger.save_logs(f"Model Registry Pipeline Started at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')}", log_level='info')

def get_current_experiment_info(file_path: str) -> dict:
    try:
        with open(file_path,'r') as file:
            exp_info = json.load(file)
        logger.debug('Experiment info loaded from %s', file_path)
        registry_logger.save_logs(f"Experiment info loaded from {file_path}", log_level='info')
    except FileNotFoundError:
        logger.error('File not found: %s', file_path)
        registry_logger.save_logs(f"File not found: {file_path}", log_level='error')
        raise
    except json.JSONDecodeError as e:
        logger.error('Failed to parse the JSON file: %s', e)
        registry_logger.save_logs(f"Failed to parse the JSON file: {e}", log_level='error')
        raise
    except Exception as e:
        logger.error('Unexpected error occurred while loading the experiment info: %s', e)
        registry_logger.save_logs(f"Unexpected error occurred while loading the experiment info: {e}", log_level='error')
        raise
    else:
        return exp_info

def model_registration(model_id:str , model_name:str , client:MlflowClient)-> None:
    try:
        model_uri = f"models:/{model_id}"
        model_version = mlflow.register_model(model_uri, model_name)
        client.transition_model_version_stage(
            name = model_name,
            version = model_version.version,
            stage = "Staging",
            archive_existing_versions = False
        )

        client.update_model_version(
            name = model_name,
            version = model_version.version,
            description = f"Model version {model_version.version} registered and transitioned to Staging."
        )

        client.set_model_version_tag(
            name = model_name,
            version = model_version.version,
            key = "author",
            value = "Avanindra Bose"
        )

        logger.debug('Model registered with ID %s and transitioned to Staging', model_id)
        registry_logger.save_logs(f"Model registered with ID {model_id} and transitioned to Staging", log_level='info')
    except Exception as e:
        logger.error('Failed to register the model: %s', e)
        registry_logger.save_logs(f"Failed to register the model: {e}", log_level='error')
        raise

def main():
    try:
        root_path = Path(__file__).parent.parent.parent
        exp_info_path = root_path / 'reports' / 'experiments_info.json'
        exp_info = get_current_experiment_info(exp_info_path)
        model_id = exp_info.get('model_id')
        model_name = "model"
        if model_id :
            model_registration(model_id,model_name,client=client)
        else :
            logger.error('Run ID not found in the experiment info.')
            registry_logger.save_logs("Run ID not found in the experiment info.", log_level='error')
    except Exception as e:
        logger.error('Failed to complete the model registration process: %s', e)
        registry_logger.save_logs(f"Failed to complete the model registration process: {e}", log_level='error')

if __name__ == "__main__":
    main()
