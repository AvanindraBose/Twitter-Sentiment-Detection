import numpy as np
import pandas as pd
import re
import nltk
import string
import logging
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from pathlib import Path
from src.logger_class import CustomLogger,create_log_path
from datetime import datetime,timezone


# logging configuration
logger = logging.getLogger('data_transformation')
logger.setLevel('DEBUG')

console_handler = logging.StreamHandler()
console_handler.setLevel('DEBUG')


formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

# File Hnadler Configuration
log_file_path = create_log_path("Data-Preprocessing")
preprocessor_logger = CustomLogger(
    logger_name="Data Preprocessing",
    log_filename=log_file_path
)

preprocessor_logger.set_log_level(level=logging.INFO)

preprocessor_logger.save_logs(f"Data Preprocessing Pipeline Started at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')}", log_level='info')

nltk.download('wordnet')
nltk.download('stopwords')

def lemmatization(text):
    """Lemmatize the text."""
    lemmatizer = WordNetLemmatizer()
    text = text.split()
    text = [lemmatizer.lemmatize(word) for word in text]
    return " ".join(text)

def remove_stop_words(text):
    """Remove stop words from the text."""
    stop_words = set(stopwords.words("english"))
    text = [word for word in str(text).split() if word not in stop_words]
    return " ".join(text)

def removing_numbers(text):
    """Remove numbers from the text."""
    text = ''.join([char for char in text if not char.isdigit()])
    return text

def lower_case(text):
    """Convert text to lower case."""
    text = text.split()
    text = [word.lower() for word in text]
    return " ".join(text)

def removing_punctuations(text):
    """Remove punctuations from the text."""
    text = re.sub('[%s]' % re.escape(string.punctuation), ' ', text)
    text = text.replace('؛', "")
    text = re.sub('\s+', ' ', text).strip()
    return text

def removing_urls(text):
    """Remove URLs from the text."""
    url_pattern = re.compile(r'https?://\S+|www\.\S+')
    return url_pattern.sub(r'', text)

def remove_small_sentences(text):
    """Remove sentences with less than 3 words."""
    if len(text.split()) < 3:
        return np.nan
    return text

def normalize_text(df):
    """Normalize the text data."""
    try:
        df['content'] = df['content'].apply(lower_case)
        logger.debug('converted to lower case')
        preprocessor_logger.save_logs(f"Text converted to lower case", log_level='info')
        df['content'] = df['content'].apply(remove_stop_words)
        logger.debug('stop words removed')
        preprocessor_logger.save_logs(f"Stop words removed", log_level='info')
        df['content'] = df['content'].apply(removing_numbers)
        logger.debug('numbers removed')
        preprocessor_logger.save_logs(f"Numbers removed", log_level='info')
        df['content'] = df['content'].apply(removing_punctuations)
        logger.debug('punctuations removed')
        preprocessor_logger.save_logs(f"Punctuations removed", log_level='info')
        df['content'] = df['content'].apply(removing_urls)
        logger.debug('urls')
        preprocessor_logger.save_logs(f"URLs removed", log_level='info')
        df['content'] = df['content'].apply(lemmatization)
        logger.debug('lemmatization performed')
        preprocessor_logger.save_logs(f"Lemmatization performed", log_level='info')
        df['content'] = df['content'].apply(remove_small_sentences)
        logger.debug('small sentences removed')
        preprocessor_logger.save_logs(f"Small sentences removed", log_level='info')

        df.dropna(inplace=True)
        logger.debug('NaN values dropped')
        preprocessor_logger.save_logs(f"NaN values dropped", log_level='info')

        return df

    except Exception as e:
        logger.error('Error during text normalization: %s', e)
        raise

def main():
    from pathlib import Path

try:
    # Fetch the data from data/raw
    train_data = pd.read_csv(Path("data/raw/train.csv"))
    test_data = pd.read_csv(Path("data/raw/test.csv"))
    logger.debug('data loaded properly')

    # Transform the data
    train_processed_data = normalize_text(train_data)
    test_processed_data = normalize_text(test_data)

    # Store the data inside data/interim
    data_path = Path("data") / "interim"
    data_path.mkdir(parents=True, exist_ok=True)
    
    train_processed_data.to_csv(data_path / "train_processed.csv", index=False)
    test_processed_data.to_csv(data_path / "test_processed.csv", index=False)
    
    logger.debug('Processed data saved to %s', data_path)
    preprocessor_logger.save_logs(f"Processed data saved to {data_path}", log_level='info')

except Exception as e:
    logger.error('Failed to complete the data transformation process: %s', e)
    preprocessor_logger.save_logs(f"Failed to complete the data transformation process: {e}", log_level='error')
    print(f"Error: {e}")

if __name__ == '__main__':
    main()