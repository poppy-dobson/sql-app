#import requests
import os
import tomllib
from pydantic import BaseModel, Field
from langchain_huggingface import HuggingFaceEndpoint
from dotenv import load_dotenv
# ...

load_dotenv()

class ModelQuizQuestionOutput(BaseModel):
  # TO BE MODIFIED LATER, this is just place-holding for now
  question: str
  correct_answer: str


quiz_model = HuggingFaceEndpoint() # will be added to