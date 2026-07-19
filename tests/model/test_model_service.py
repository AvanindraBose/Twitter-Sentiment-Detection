from backend.services.model_service import removing_punctuations


def test_removing_punctuations_normalizes_whitespace():
    assert removing_punctuations("Hello,   world!") == "Hello world"
