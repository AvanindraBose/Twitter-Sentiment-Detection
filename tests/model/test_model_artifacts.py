import pandas as pd
import mlflow
from mlflow.tracking import MlflowClient
import joblib
from sklearn.metrics import accuracy_score


def test_model_artifacts_exist(trained_model):

    assert trained_model is not None , "Model Not Found"


def test_vectorizer_exist(vectorizer):

    assert vectorizer is not None , "Vectorizer Not Found"


def test_model_and_vectorizer_expose_expected_interfaces(trained_model, vectorizer):
    assert hasattr(trained_model, "predict")
    assert hasattr(vectorizer, "transform")


# def test_vectorizer_transforms_raw_texts(trained_vectorizer, sample_texts):
#     transformed = trained_vectorizer.transform(sample_texts)

#     assert transformed.shape[0] == len(sample_texts)
#     assert transformed.shape[1] > 0


# def test_model_predicts_binary_labels_on_processed_features(trained_model, processed_test_features):
#     sample_batch = processed_test_features.head(10)
#     predictions = trained_model.predict(sample_batch)

#     assert len(predictions) == len(sample_batch)
#     assert set(predictions).issubset({0, 1})


# def test_model_keeps_reasonable_accuracy_on_saved_test_split(trained_model, processed_test_features, processed_test_target):
#     sample_size = min(200, len(processed_test_features))
#     feature_batch = processed_test_features.head(sample_size)
#     target_batch = processed_test_target.head(sample_size)

#     predictions = trained_model.predict(feature_batch)
#     accuracy = accuracy_score(target_batch, predictions)

#     assert accuracy >= 0.70, f"Expected accuracy >= 0.70, got {accuracy:.3f}"


# def test_model_prediction_output_matches_feature_input_shape(trained_model, trained_vectorizer, sample_texts):
#     transformed = trained_vectorizer.transform(sample_texts)
#     feature_frame = pd.DataFrame(
#         transformed.toarray(),
#         columns=[str(index) for index in range(transformed.shape[1])],
#     )

#     predictions = trained_model.predict(feature_frame)

#     assert len(predictions) == len(sample_texts)
