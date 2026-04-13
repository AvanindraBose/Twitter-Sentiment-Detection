import numpy as np
import pandas as pd
import joblib
import yaml
import logging
from pathlib import Path
from sklearn.feature_extraction.text import CountVectorizer
from src.logger_class import  CustomLogger,create_log_path
from datetime import datetime , timezone

# logging configuration -> Console and File Configurations
logger = logging.getLogger('feature_engineering')
logger.setLevel('DEBUG')

console_handler = logging.StreamHandler()
console_handler.setLevel('DEBUG')


formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)


logger.addHandler(console_handler)

#  File Handler Configuration
log_file_path = create_log_path("Feature-Engineering")
feature_logger = CustomLogger(
    logger_name="Feature Engineering",
    log_filename=log_file_path
)

feature_logger.set_log_level(level=logging.INFO)

feature_logger.save_logs(f"Feature Engineering Pipeline Started at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')}", log_level='info')

def load_params(params_path: str) -> dict:
    """Load parameters from a YAML file."""
    try:
        with open(params_path, 'r') as file:
            params = yaml.safe_load(file)
        logger.debug('Parameters retrieved from %s', params_path)
        feature_logger.save_logs(f"Parameters retrieved from {params_path}", log_level='info')
        return params
    except FileNotFoundError:
        logger.error('File not found: %s', params_path)
        feature_logger.save_logs(f"File not found: {params_path}", log_level='error')
        raise
    except yaml.YAMLError as e:
        logger.error('YAML error: %s', e)
        feature_logger.save_logs(f"YAML error: {e}", log_level='error')
        raise
    except Exception as e:
        logger.error('Unexpected error: %s', e)
        feature_logger.save_logs(f"Unexpected error: {e}", log_level='error')
        raise

def load_data(file_path: str) -> pd.DataFrame:
    """Load data from a CSV file."""
    try:
        df = pd.read_csv(file_path)
        df.fillna('', inplace=True)
        logger.debug('Data loaded and NaNs filled from %s', file_path)
        feature_logger.save_logs(f"Data loaded and NaNs filled from {file_path}", log_level='info')
        return df
    except pd.errors.ParserError as e:
        logger.error('Failed to parse the CSV file: %s', e)
        feature_logger.save_logs(f"Failed to parse the CSV file: {e}", log_level='error')
        raise
    except Exception as e:
        logger.error('Unexpected error occurred while loading the data: %s', e)
        feature_logger.save_logs(f"Unexpected error occurred while loading the data: {e}", log_level='error')
        raise

def save_vectorizer(vectorizer: CountVectorizer, file_path: str) -> None:
    """Save the Count Vectorizer model to a file."""
    try:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'wb') as file:
            joblib.dump(vectorizer, file)
        logger.debug('Count Vectorizer saved to %s', file_path)
        feature_logger.save_logs(f"Count Vectorizer saved to {file_path}", log_level='info')
    except Exception as e:
        logger.error('Error saving Count Vectorizer: %s', e)
        feature_logger.save_logs(f"Error saving Count Vectorizer: {e}", log_level='error')
        raise

def apply_count_vectorizer(train_data: pd.DataFrame, test_data: pd.DataFrame, max_features: int , model_path:str) -> tuple:
    """Apply Count Vectorizer to the data."""
    try:
        vectorizer = CountVectorizer(max_features=max_features)

        X_train = train_data['content'].values
        y_train = train_data['sentiment'].values
        X_test = test_data['content'].values
        y_test = test_data['sentiment'].values

        X_train_bow = vectorizer.fit_transform(X_train)
        X_test_bow = vectorizer.transform(X_test)

        train_df = pd.DataFrame(X_train_bow.toarray())
        train_df['label'] = y_train

        test_df = pd.DataFrame(X_test_bow.toarray())
        test_df['label'] = y_test
        
        save_vectorizer(vectorizer,model_path/"vectorizer.joblib")

        logger.debug('Count Vectorizer applied and data transformed')
        feature_logger.save_logs(f"Count Vectorizer applied and data transformed", log_level='info')
        return train_df, test_df
    except Exception as e:
        logger.error('Error during Count Vectorizer transformation: %s', e)
        feature_logger.save_logs(f"Error during Count Vectorizer transformation: {e}", log_level='error')
        raise

def save_data(df: pd.DataFrame, file_path: str) -> None:
    """Save the dataframe to a CSV file."""
    try:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        df.to_csv(file_path, index=False)
        logger.debug('Data saved to %s', file_path)

    except Exception as e:
        logger.error('Unexpected error occurred while saving the data: %s', e)
        raise


def main():
    try:
        params = load_params('params.yaml')
        max_features = params['feature_engineering']['max_features']
        root_path = Path(__file__).parent.parent.parent
        model_path = root_path/"models"

        train_data = load_data(Path("data/interim/train_processed.csv"))
        test_data = load_data(Path("data/interim/test_processed.csv"))

        train_df, test_df = apply_count_vectorizer(train_data, test_data, max_features,model_path)

        save_data(train_df, Path("data") / "processed" / "train_bow.csv")
        save_data(test_df, Path("data") / "processed" / "test_bow.csv")

    except Exception as e:
        logger.error('Failed to complete the feature engineering process: %s', e)
        print(f"Error: {e}")

if __name__ == '__main__':
    main()