import mlflow
import os
import logging
from mlflow.tracking import MlflowClient
from dotenv import load_dotenv
from src.logger_class import CustomLogger,create_log_path 
from datetime import datetime,timezone


# File Handler configurations
log_file_path = create_log_path("Model-Promotion")
model_promotion_logger = CustomLogger(
    logger_name="Model-Promotion",
    log_filename= log_file_path
)

model_promotion_logger.set_log_level(level=logging.INFO)

model_promotion_logger.save_logs(f"Model Promotion Script Triggered at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')}", log_level='info')

def get_token() -> str:
    try:
        token = os.getenv("DAGSHUB_PAT")
    except Exception as e:
        model_promotion_logger.save_logs("DAGSHUB token not found in env file",log_level='warning')
        raise
    
def get_client() -> MlflowClient:
    dagshub_token = get_token()
    os.environ["MLFLOW_TRACKING_USERNAME"] = dagshub_token
    os.environ["MLFLOW_TRACKING_PASSWORD"] = dagshub_token

    dagshub_url = "https://dagshub.com"
    repo_owner = "AvanindraBose"
    repo_name = "Twitter-Sentiment-Detection"

# Set up MLflow tracking URI
    mlflow.set_tracking_uri(f'{dagshub_url}/{repo_owner}/{repo_name}.mlflow')

    client = MlflowClient()
    
    model_promotion_logger.save_logs('Successfully Initiated Dagshub Session',log_level='info')

    return client

def get_latest_staging_model_version(client:MlflowClient , model=str):
    try:
        stage_model = client.get_latest_versions(name=model , stages=['Staging'])[0]

    except Exception as e:
        model_promotion_logger.save_logs(f"Staging Model Version Not Found due to :{str(e)}",log_level='error')
        raise
    
    else:
        model_promotion_logger.save_logs("Staging Model Version Loaded Successfully",log_level='info')

        return stage_model.version

def promote_staging_model(client,stage_model_version,model_name) :
    try: 
        client.transition_model_version_stage(
        name = model_name,
        version = stage_model_version,
        stage = 'Production',
        archive_existing_versions=True
    )
    
    except Exception as e :
        model_promotion_logger.save_logs(f'Model Promotion of Staging Model version {stage_model_version} is not promoted to Production',
                                         log_level='error')
        raise
    
    else :
        model_promotion_logger.save_logs(f'Model Promotion of Staging model version {stage_model_version} is successfully moved to production',
                                         log_level='info')

def main(): 

    client = get_client()

    model_name = "model"

    stage_model_version = get_latest_staging_model_version(client , model_name)

    promote_staging_model(client,stage_model_version,model_name)

if __name__ == "__main__":
    main()