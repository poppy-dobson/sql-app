import pytest
from dotenv import find_dotenv, load_dotenv
import os

from model import SQLQuizLLM, verify_api_key, _verify_hf_api_key, ModelQuizQuestionOutput, ListOfQuizQuestions, quiz_question_parser, ModelFeedback, feedback_parser

# @pytest.fixture(scope='session', autouse=True)
# def load_env() -> None:
#     load_dotenv()

@pytest.fixture(scope="class")
def valid_hf_api_key():
  load_dotenv()
  return os.environ.get("HUGGINGFACEHUB_API_TOKEN")

@pytest.fixture(scope="class")
def model():
  # temp
  return None

class TestAPIKeys:

  def test_api_key_verification(self, valid_hf_api_key):
    load_dotenv()
    assert verify_api_key("blah") == False
    assert verify_api_key(valid_hf_api_key) == True

class TestModel:
  pass

class TestDB:
  pass

class TestSQLiteDB:
  pass

def test_test():
  assert 1 == 1
