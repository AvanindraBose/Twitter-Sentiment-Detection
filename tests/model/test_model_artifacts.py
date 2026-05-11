import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score


def test_model_artifacts_exist(trained_model):

    assert trained_model is not None , "Model Not Found"


def test_vectorizer_exist(vectorizer):

    assert vectorizer is not None , "Vectorizer Not Found"


def test_model_and_vectorizer_expose_expected_interfaces(trained_model, vectorizer):
    assert hasattr(trained_model, "predict")
    assert hasattr(vectorizer, "transform")


def test_model_signature(trained_model, vectorizer, sample_input_text):
    input_data = vectorizer.transform([sample_input_text])
    input_df = pd.DataFrame(
        input_data.toarray(),
        columns=[str(index) for index in range(input_data.shape[1])],
    )
    prediction = trained_model.predict(input_df)

    assert input_df.shape[1] == len(vectorizer.get_feature_names_out())
    assert len(prediction) == input_df.shape[0]
    assert len(prediction.shape) == 1


def test_model_performance(trained_model, production_holdout_data):
    x_holdout = production_holdout_data.iloc[:, 0:-1]
    y_holdout = production_holdout_data.iloc[:, -1]
    y_pred_new = trained_model.predict(x_holdout)

    accuracy_new = accuracy_score(y_holdout, y_pred_new)
    precision_new = precision_score(y_holdout, y_pred_new)
    recall_new = recall_score(y_holdout, y_pred_new)
    f1_new = f1_score(y_holdout, y_pred_new)

    expected_accuracy = 0.70
    expected_precision = 0.70
    expected_recall = 0.70
    expected_f1 = 0.70

    assert accuracy_new >= expected_accuracy, f"Accuracy should be at least {expected_accuracy}"
    assert precision_new >= expected_precision, f"Precision should be at least {expected_precision}"
    assert recall_new >= expected_recall, f"Recall should be at least {expected_recall}"
    assert f1_new >= expected_f1, f"F1 score should be at least {expected_f1}"


def test_model_prediction_count_matches_input_rows(trained_model, production_sample_features, sample_text_batch):
    predictions = trained_model.predict(production_sample_features)

    assert len(predictions) == len(sample_text_batch)
