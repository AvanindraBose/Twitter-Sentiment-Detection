from pydantic import BaseModel

class RequestSchema(BaseModel):
    text : str

class ResponseSchema(BaseModel):
    sentiment : str
