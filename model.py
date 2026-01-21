#import requests
import os
import tomllib
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from dotenv import load_dotenv
# ...

# set-up

load_dotenv()

hf_api_key = os.environ['HUGGINGFACEHUB_API_TOKEN']

with open("app_config.toml", "rb") as config_file:
  config = tomllib.load(config_file)

###

class SQLQuizLLM: # overall handling of the whole process
  def __init__(self):
    pass

input_template = """
You are a ...

The database to use has the following schema:
{schema}

Generate {num_questions}
"""

sql_quiz_prompt_template = PromptTemplate(
  input_variables=["schema", "topics", "num_questions"],
  template=input_template
)

class ModelQuizQuestionOutput(BaseModel):
  # TO BE MODIFIED LATER, this is just place-holding for now
  question: str
  correct_sql_answer: str # this should have validation to ensure it's an SQL SELECT statement

# test for now
temp_quiz_model = HuggingFaceEndpoint(
  repo_id="defog/llama-3-sqlcoder-8b", provider="featherless-ai",
  #repo_id="Qwen/Qwen3-4B-Instruct-2507", provider="nscale",
  #repo_id="openai/gpt-oss-20b", provider="novita", 
  temperature=0.5,
  max_new_tokens=256,
  huggingfacehub_api_token=hf_api_key
) # will be added to

temp_chat = ChatHuggingFace(llm=temp_quiz_model) # note to self: find another way of doing this at some point - i don't like the fact it has to use the conversation task

test_response = temp_chat.invoke("respond with one word.")
print(test_response.content)