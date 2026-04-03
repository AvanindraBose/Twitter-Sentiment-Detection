import numpy as np
import pandas as pd
import joblib
import yaml
import logging
from sklearn.ensemble import GradientBoostingClassifier
from src.logger_class import CustomLogger,create_log_path
from datetime import datetime , timezone


# logging configuration -> Console and File Configurations
logger = logging.getLogger('model_building')
logger.setLevel('DEBUG')

console_handler = logging.StreamHandler()
console_handler.setLevel('DEBUG')


formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

# File Handler Configuration
log_file_path = create_log_path("Model Building")
training_logger = CustomLogger(
    logger_name="Training",
    log_filename=log_file_path
)

training_logger.set_log_level(level=logging.INFO)

training_logger.save_logs(f"Model Building Pipeline Started at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')}", log_level='info')

def load_params(params_path: str) -> dict:
    """Load parameters from a YAML file."""
    try:
        with open(params_path, 'r') as file:
            params = yaml.safe_load(file)
        logger.debug('Parameters retrieved from %s', params_path)
        training_logger.save_logs(f"Parameters retrieved from {params_path}", log_level='info')
        return params
    except FileNotFoundError:
        logger.error('File not found: %s', params_path)
        training_logger.save_logs(f"File not found: {params_path}", log_level='error')
        raise
    except yaml.YAMLError as e:
        logger.error('YAML error: %s', e)
        training_logger.save_logs(f"YAML error: {e}", log_level='error')
        raise
    except Exception as e:
        logger.error('Unexpected error: %s', e)
        training_logger.save_logs(f"Unexpected error: {e}", log_level='error')
        raise

def load_data(file_path: str) -> pd.DataFrame:
    """Load data from a CSV file."""
    try:
        df = pd.read_csv(file_path)
        logger.debug('Data loaded from %s', file_path)
        training_logger.save_logs(f"Data loaded from {file_path}", log_level='info')
        return df
    except pd.errors.ParserError as e:
        logger.error('Failed to parse the CSV file: %s', e)
        training_logger.save_logs(f"Failed to parse the CSV file: {e}", log_level='error')
        raise
    except Exception as e:
        logger.error('Unexpected error occurred while loading the data: %s', e)
        training_logger.save_logs(f"Unexpected error occurred while loading the data: {e}", log_level='error')
        raise

def train_model(X_train: np.ndarray, y_train: np.ndarray, params: dict) -> GradientBoostingClassifier:
    """Train the Gradient Boosting model."""
    try:
        clf = GradientBoostingClassifier(n_estimators=params['n_estimators'], learning_rate=params['learning_rate'])
        clf.fit(X_train, y_train)
        logger.debug('Model training completed')
        training_logger.save_logs(f"Model training completed with parameters: n_estimators={params['n_estimators']}, learning_rate={params['learning_rate']}", log_level='info')
        return clf
    except Exception as e:
        logger.error('Error during model training: %s', e)
        training_logger.save_logs(f"Error during model training: {e}", log_level='error')
        raise

def save_model(model, file_path: str) -> None:
    """Save the trained model to a file."""
    try:
        with open(file_path, 'wb') as file:
            joblib.dump(model, file)
        logger.debug('Model saved to %s', file_path)
        training_logger.save_logs(f"Model saved to {file_path}", log_level='info')
    except Exception as e:
        logger.error('Error occurred while saving the model: %s', e)
        training_logger.save_logs(f"Error occurred while saving the model: {e}", log_level='error')
        raise

def main():
    try:
        params = load_params('params.yaml')['model_building']

        train_data = load_data('./data/processed/train_tfidf.csv')
        X_train = train_data.iloc[:, :-1].values
        y_train = train_data.iloc[:, -1].values

        clf = train_model(X_train, y_train, params)
        
        save_model(clf, 'models/model.joblib')
    except Exception as e:
        logger.error('Failed to complete the model building process: %s', e)
        training_logger.save_logs(f"Failed to complete the model building process: {e}", log_level='error')
        print(f"Error: {e}")

if __name__ == '__main__':
    main()