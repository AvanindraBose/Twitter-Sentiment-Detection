import numpy as np
import pandas as pd
import joblib
import mlflow
import mlflow.sklearn
import dagshub
import json
import os
import logging
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
from datetime import datetime, timezone
from src.logger_class import CustomLogger, create_log_path

mlflow.set_tracking_uri(os.getenv('MLFLOW_TRACKING_URI'))
dagshub.init(repo_owner='AvanindraBose', repo_name='Twitter-Sentiment-Detection', mlflow=True)

# logging configuration
logger = logging.getLogger('model_evaluation')
logger.setLevel('DEBUG')

console_handler = logging.StreamHandler()
console_handler.setLevel('DEBUG')

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)


logger.addHandler(console_handler)

# File Handler Configuration
log_file_path = create_log_path("Model Evaluation")
evaluation_logger = CustomLogger(
    logger_name="Evaluation",
    log_filename=log_file_path
)

evaluation_logger.set_log_level(level=logging.INFO)

evaluation_logger.save_logs(f"Model Evaluation Pipeline Started at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')}", log_level='info')

def load_model(file_path: str):
    """Load the trained model from a file."""
    try:
        with open(file_path, 'rb') as file:
            model = joblib.load(file)
        logger.debug('Model loaded from %s', file_path)
        evaluation_logger.save_logs(f"Model loaded from {file_path}", log_level='info')
        return model
    except FileNotFoundError:
        logger.error('File not found: %s', file_path)
        evaluation_logger.save_logs(f"File not found: {file_path}", log_level='error')
        raise
    except Exception as e:
        logger.error('Unexpected error occurred while loading the model: %s', e)
        evaluation_logger.save_logs(f"Unexpected error occurred while loading the model: {e}", log_level='error')
        raise

def load_data(file_path: str) -> pd.DataFrame:
    """Load data from a CSV file."""
    try:
        df = pd.read_csv(file_path)
        logger.debug('Data loaded from %s', file_path)
        evaluation_logger.save_logs(f"Data loaded from {file_path}", log_level='info')
        return df
    except pd.errors.ParserError as e:
        logger.error('Failed to parse the CSV file: %s', e)
        evaluation_logger.save_logs(f"Failed to parse the CSV file: {e}", log_level='error')
        raise
    except Exception as e:
        logger.error('Unexpected error occurred while loading the data: %s', e)
        evaluation_logger.save_logs(f"Unexpected error occurred while loading the data: {e}", log_level='error')
        raise

def evaluate_model(clf, X_test: np.ndarray, y_test: np.ndarray) -> dict:
    """Evaluate the model and return the evaluation metrics."""
    try:
        y_pred = clf.predict(X_test)
        y_pred_proba = clf.predict_proba(X_test)[:, 1]

        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_pred_proba)

        metrics_dict = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'auc': auc
        }
        logger.debug('Model evaluation metrics calculated')
        evaluation_logger.save_logs(f"Model evaluation metrics calculated: {metrics_dict}", log_level='info')
        return metrics_dict
    except Exception as e:
        logger.error('Error during model evaluation: %s', e)
        evaluation_logger.save_logs(f"Error during model evaluation: {e}", log_level='error')
        raise

def save_metrics(metrics: dict, file_path: str) -> None:
    """Save the evaluation metrics to a JSON file."""
    try:
        with open(file_path, 'w') as file:
            json.dump(metrics, file, indent=4)
        logger.debug('Metrics saved to %s', file_path)
        evaluation_logger.save_logs(f"Metrics saved to {file_path}", log_level='info')
    except Exception as e:
        logger.error('Error occurred while saving the metrics: %s', e)
        evaluation_logger.save_logs(f"Error occurred while saving the metrics: {e}", log_level='error')
        raise

def save_run_info(run_id: str, file_path: str) -> None:
    """Save the MLflow run information to a JSON file."""
    try:
        run_info = mlflow.get_run(run_id).info
        run_data = {
            'run_id': run_info.run_id,
            'experiment_id': run_info.experiment_id,
            # 'status': run_info.status,
            # 'start_time': run_info.start_time,
            # 'end_time': run_info.end_time,
            # 'duration': (run_info.end_time - run_info.start_time) / 1000  # duration in seconds
        }
        with open(file_path, 'w') as file:
            json.dump(run_data, file, indent=4)
        logger.debug('Run information saved to %s', file_path)
        evaluation_logger.save_logs(f"Run information saved to {file_path}", log_level='info')
    except Exception as e:
        logger.error('Error occurred while saving the run information: %s', e)
        evaluation_logger.save_logs(f"Error occurred while saving the run information: {e}", log_level='error')
        raise

def main():
    mlflow.set_experiment("twitter-sentiment-dvc-pipeline")
    with mlflow.start_run(run_name = "LR Model Logging") as run :
        try:
            clf = load_model('./models/model.joblib')
            test_data = load_data('./data/processed/test_bow.csv')
        
            X_test = test_data.iloc[:, :-1].values
            y_test = test_data.iloc[:, -1].values

            metrics = evaluate_model(clf, X_test, y_test)
        
            save_metrics(metrics, 'reports/metrics.json')

            for metric_name , metric_value in metrics.items():
                mlflow.log_metric(metric_name, metric_value)
            
            if hasattr(clf, 'get_params'):
                params = clf.get_params()
                for param_name, param_value in params.items():
                    mlflow.log_param(param_name, param_value)
            save_run_info(run.info.run_id,'reports/experiments_info.json')
            mlflow.sklearn.log_model(clf, "model")
            mlflow.log_artifact('reports/metrics.json')
            mlflow.log_artifact('reports/experiments_info.json')
            # mlflow.log_artifact('model_evaluation_errors.log')
        except Exception as e:
            logger.error('Failed to complete the model evaluation process: %s', e)
            evaluation_logger.save_logs(f"Failed to complete the model evaluation process: {e}", log_level='error')

if __name__ == '__main__':
    main()