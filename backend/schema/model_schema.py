from pydantic import BaseModel, Field


class RequestSchema(BaseModel):
    text: str


class ResponseSchema(BaseModel):
    sentiment: int


class XquikTweetRow(BaseModel):
    id: str | int | None = None
    tweet_id: str | int | None = None
    text: str | None = None
    tweet_text: str | None = None
    full_text: str | None = None
    content: str | None = None

    def readable_text(self) -> str:
        for value in (self.text, self.tweet_text, self.full_text, self.content):
            if value and value.strip():
                return value.strip()

        return ""

    def source_id(self) -> str | None:
        value = self.tweet_id if self.tweet_id is not None else self.id
        if value is None:
            return None

        return str(value)


class XquikBatchRequest(BaseModel):
    tweets: list[XquikTweetRow] = Field(min_length=1, max_length=100)


class XquikPrediction(BaseModel):
    index: int
    source_id: str | None = None
    sentiment: int


class XquikBatchResponse(BaseModel):
    predictions: list[XquikPrediction]
