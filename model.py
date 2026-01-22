#import requests
import os
import tomllib
from pydantic import BaseModel, Field, field_validator
from typing import List
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
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


class ModelQuizQuestionOutput(BaseModel):
  quiz_question: str
  correct_sql_answer: str

  @field_validator('correct_sql_answer', mode = 'after')
  @classmethod
  def validate_sql_answer(cls, query: str):
    first_word = query.split()[0].upper()
    if (first_word not in ['CREATE', 'INSERT', 'UPDATE', 'ALTER', 'SELECT', 'WITH']) or query[-1] != ';':
      raise ValueError('not a valid SQL query')
    return query

class ListOfQuizQuestions(BaseModel):
  questions_and_answers: List[ModelQuizQuestionOutput]

quiz_question_parser = PydanticOutputParser(pydantic_object=ListOfQuizQuestions)

input_template = """
You are setting an SQL quiz, with {num_questions} questions.

The database to use for questions has the following schema:
{schema}

Generate a list of {num_questions} question & answer pairs.
Each question should ask the user to write a query specific to this database, and the answer is an SQL query that is the correct solution to the question.
Questions should explicitly tell the user which columns to return, and the correct answers MUST incorpate at least one of the following SQL query aspects: {topics}.
Answer queries should end in a semi-colon, and be written in one line with no breaks.

Ensure that answer queries are correct, and involve at least one of the topics given.

{format_instruction}

Return nothing but a valid JSON document described above.
"""

# Respond with nothing else but the output in the following format, as JSON:

sql_quiz_prompt_template = PromptTemplate(
  input_variables=["schema", "topics", "num_questions"],
  template=input_template,
  partial_variables={'format_instruction': quiz_question_parser.get_format_instructions()}
)

#####################################
# test for now
temp_quiz_model = HuggingFaceEndpoint(
  #repo_id="defog/llama-3-sqlcoder-8b", provider="featherless-ai", # does output wrong and worse
  #repo_id="Qwen/Qwen3-4B-Instruct-2507", provider="nscale", 
  repo_id="Qwen/Qwen2.5-Coder-32B-Instruct", provider="nscale", # BEST ONE SO FAR
  #repo_id="openai/gpt-oss-20b", provider="novita", 
  temperature=0.7,
  max_new_tokens=768,
  huggingfacehub_api_token=hf_api_key
) # will be added to

temp_chat = ChatHuggingFace(llm=temp_quiz_model) # note to self: find another way of doing this at some point - i don't like the fact it has to use the conversation task

quiz_chain = sql_quiz_prompt_template | temp_chat | quiz_question_parser

test_response = quiz_chain.invoke({"schema": """
CREATE TABLE platform (
        id INTEGER PRIMARY KEY,
        platform_name TEXT DEFAULT NULL
);
CREATE TABLE genre (
        id INTEGER PRIMARY KEY,
        genre_name TEXT DEFAULT NULL
);
CREATE TABLE publisher (
        id INTEGER PRIMARY KEY,
        publisher_name TEXT DEFAULT NULL
);
CREATE TABLE region (
        id INTEGER PRIMARY KEY,
        region_name TEXT DEFAULT NULL
);
CREATE TABLE game (
        id INTEGER PRIMARY KEY,
        genre_id INTEGER,
        game_name TEXT DEFAULT NULL,
        CONSTRAINT fk_gm_gen FOREIGN KEY (genre_id) REFERENCES genre(id)
);
CREATE TABLE game_publisher (
        id INTEGER PRIMARY KEY,
        game_id INTEGER DEFAULT NULL,
        publisher_id INTEGER DEFAULT NULL,
        CONSTRAINT fk_gpu_gam FOREIGN KEY (game_id) REFERENCES game(id),
        CONSTRAINT fk_gpu_pub FOREIGN KEY (publisher_id) REFERENCES publisher(id)
);
CREATE TABLE game_platform (
        id INTEGER PRIMARY KEY,
        game_publisher_id INTEGER DEFAULT NULL,
        platform_id INTEGER DEFAULT NULL,
        release_year INTEGER DEFAULT NULL,
        CONSTRAINT fk_gpl_gp FOREIGN KEY (game_publisher_id) REFERENCES game_publisher(id),
        CONSTRAINT fk_gpl_pla FOREIGN KEY (platform_id) REFERENCES platform(id)
);
CREATE TABLE region_sales (
        region_id INTEGER DEFAULT NULL,
        game_platform_id INTEGER DEFAULT NULL,
        num_sales REAL,
   CONSTRAINT fk_rs_gp FOREIGN KEY (game_platform_id) REFERENCES game_platform(id),
        CONSTRAINT fk_rs_reg FOREIGN KEY (region_id) REFERENCES region(id)
);
""",
                                   "topics": str(["Aggregate Functions", "GROUP BY", "Subqueries", "EXISTS / NOT EXISTS",
          "'Double NOT EXISTS' (Nested NOT EXISTS)"]),
                                   "num_questions": str(3)})


for question in test_response.questions_and_answers:
  print(question.quiz_question)
  print(question.correct_sql_answer)

#print(quiz_question_parser.get_format_instructions())