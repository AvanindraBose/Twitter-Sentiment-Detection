import numpy as np
import pandas as pd
import os
import re
import nltk
import string
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from backend.core.dependencies import load_artifacts
from backend.logging_fastapi.logger_api import prediction_logger

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

def remove_small_sentences(df):
    """Remove sentences with less than 3 words."""
    for i in range(len(df)):
        if len(df.text.iloc[i].split()) < 3:
            df.text.iloc[i] = np.nan

def normalize_text(text):
    text = lower_case(text)
    text = remove_stop_words(text)
    text = removing_numbers(text)
    text = removing_punctuations(text)
    text = removing_urls(text)
    text = lemmatization(text)

    return text

def predict_sentiment(data: dict) -> dict:

    prediction_logger.save_logs("Prediction pipeline started", "info")

    try:
        text = data.get("text")

        if not text:
            raise ValueError("Input text is empty")

        prediction_logger.save_logs("Input received for prediction", "info")

    except Exception as e:
        prediction_logger.save_logs(
            f"[INPUT ERROR] Failed to read input: {str(e)}", "error"
        )
        raise

    try:
        model, vectorizer = load_artifacts()
        prediction_logger.save_logs("Model and vectorizer loaded", "info")

    except Exception as e:
        prediction_logger.save_logs(
            f"[MODEL LOAD ERROR] {str(e)}", "error"
        )
        raise

    try:
        normalized_text = normalize_text(text)
        prediction_logger.save_logs("Text normalization completed", "info")

    except Exception as e:
        prediction_logger.save_logs(
            f"[PREPROCESS ERROR] {str(e)}", "error"
        )
        raise

    try:
        features = vectorizer.transform([normalized_text])
        prediction_logger.save_logs("Vectorization successful", "info")

    except Exception as e:
        prediction_logger.save_logs(
            f"[VECTORIZATION ERROR] {str(e)}", "error"
        )
        raise

    try:
        # Only ONE conversion needed
        features_df = pd.DataFrame(
            features.toarray(),
            columns=[str(i) for i in range(features.shape[1])]
        )

        prediction = model.predict(features_df)

        prediction_logger.save_logs(
            f"Prediction completed successfully | Output={prediction[0]}",
            "info"
        )

        return {"prediction": prediction[0]}

    except Exception as e:
        prediction_logger.save_logs(
            f"[PREDICTION ERROR] {str(e)}", "error"
        )
        raise
