import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
import yaml
import logging
from src.logger_class import CustomLogger,create_log_path
from datetime import datetime , timezone
from pathlib import Path

# logging configuration -> Console and File Configurations
logger = logging.getLogger('data_ingestion')
logger.setLevel('DEBUG')

console_handler = logging.StreamHandler()
console_handler.setLevel('DEBUG')


formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)


# Logging File Configurations
log_file_path = create_log_path("Ingest Data")
dataset_logger = CustomLogger(
    logger_name="Training",
    log_filename=log_file_path
)

dataset_logger.set_log_level(level=logging.INFO)

dataset_logger.save_logs(f"Make Dataset Pipeline Started at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')}", log_level='info')

def load_params(params_path: str) -> dict:
    """Load parameters from a YAML file."""
    try:
        with open(params_path, 'r') as file:
            params = yaml.safe_load(file)
        logger.debug('Parameters retrieved from %s', params_path)
        dataset_logger.save_logs(f"Parameters retrieved from {params_path}", log_level='info')
        return params
    except FileNotFoundError:
        logger.error('File not found: %s', params_path)
        dataset_logger.save_logs(f"File not found: {params_path}", log_level='error')
        raise
    except yaml.YAMLError as e:
        logger.error('YAML error: %s', e)
        dataset_logger.save_logs(f"YAML error: {e}", log_level='error')
        raise
    except Exception as e:
        logger.error('Unexpected error: %s', e)
        dataset_logger.save_logs(f"Unexpected error: {e}", log_level='error')
        raise

def load_data(data_url: str) -> pd.DataFrame:
    """Load data from a CSV file."""
    try:
        df = pd.read_csv(data_url)
        logger.debug('Data loaded from %s', data_url)
        dataset_logger.save_logs(f"Data loaded from {data_url}", log_level='info')
        return df
    except pd.errors.ParserError as e:
        logger.error('Failed to parse the CSV file: %s', e)
        dataset_logger.save_logs(f"Failed to parse the CSV file: {e}", log_level='error')
        raise
    except Exception as e:
        logger.error('Unexpected error occurred while loading the data: %s', e)
        dataset_logger.save_logs(f"Unexpected error occurred while loading the data: {e}", log_level='error')
        raise

def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """Preprocess the data."""
    try:
        df.drop(columns=['tweet_id'], inplace=True)
        final_df = df[df['sentiment'].isin(['happiness', 'sadness'])]
        final_df['sentiment'].replace({'happiness': 1, 'sadness': 0}, inplace=True)
        logger.debug('Data preprocessing completed')
        dataset_logger.save_logs("Data preprocessing completed", log_level='info')
        return final_df
    except KeyError as e:
        logger.error('Missing column in the dataframe: %s', e)
        dataset_logger.save_logs(f"Missing column in the dataframe: {e}", log_level='error')
        raise
    except Exception as e:
        logger.error('Unexpected error during preprocessing: %s', e)
        dataset_logger.save_logs(f"Unexpected error during preprocessing: {e}", log_level='error')
        raise

def save_data(train_data: pd.DataFrame, test_data: pd.DataFrame, data_path: str) -> None:
    """Save the train and test datasets."""
    from pathlib import Path

def save_data(train_data: pd.DataFrame, test_data: pd.DataFrame, data_path: str) -> None:
    """Save the train and test datasets."""
    try:
        raw_data_path = Path(data_path) / "raw"
        raw_data_path.mkdir(parents=True, exist_ok=True)

        train_data.to_csv(raw_data_path / "train.csv", index=False)
        test_data.to_csv(raw_data_path / "test.csv", index=False)

        logger.debug('Train and test data saved to %s', raw_data_path)
        dataset_logger.save_logs(f"Train and test data saved to {raw_data_path}", log_level='info')

    except Exception as e:
        logger.error('Unexpected error occurred while saving the data: %s', e)
        dataset_logger.save_logs(f"Unexpected error occurred while saving the data: {e}", log_level='error')
        raise

def main():
    try:
        params = load_params(params_path='params.yaml')
        test_size = params['data_ingestion']['test_size']
        
        df = load_data(data_url='https://raw.githubusercontent.com/campusx-official/jupyter-masterclass/main/tweet_emotions.csv')
        final_df = preprocess_data(df)
        train_data, test_data = train_test_split(final_df, test_size=test_size, random_state=42)
        save_data(train_data, test_data, data_path='./data')
        dataset_logger.save_logs(f"Make Dataset Pipeline Completed at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')}", log_level='info')
    except Exception as e:
        logger.error('Failed to complete the data ingestion process: %s', e)
        dataset_logger.save_logs(f"Failed to complete the data ingestion process: {e}", log_level='error')
        print(f"Error: {e}")

if __name__ == '__main__':
    main()