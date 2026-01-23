#import requests
import os
import re
from pydantic import BaseModel, Field, field_validator
from typing import List
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from dotenv import load_dotenv
# ...

from util import load_app_config

# set-up

load_dotenv()

hf_api_key = os.environ['HUGGINGFACEHUB_API_TOKEN']

####################################################

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

class SQLQuizLLM: # overall handling of the whole process
  def __init__(self, config_dict):
    self.config = config_dict
    self.model = self.set_model()

    self.quiz_prompt_template = self.set_prompt_template()
    self.num_questions = self.config['quiz']['num_questions']


    self.quiz_chain = self.quiz_prompt_template | self.model | quiz_question_parser

  def set_model(self):
    if self.config['model']['endpoint'] == 'hf':
      hf_endpoint = HuggingFaceEndpoint(
      repo_id=self.config['model']['repo_id'], provider=self.config['model']['provider'],
      temperature=0.8,
      max_new_tokens=768,
      huggingfacehub_api_token=hf_api_key)

      model = ChatHuggingFace(llm=hf_endpoint) # note to self: find another way of doing this at some point - i don't like the fact it has to use the conversation task
    else:
      # at the moment:
      raise ValueError("invalid/unsupported endpoint given in config")
      # but will handle other endpoints at some point 
    return model

  def generate_quiz(self, db_schema, db_rdbms, topic_list): # CHANGE THIS to just take a db object and get schema etc from that
    valid_quiz = False
    while not valid_quiz:
      try:
        response = self._get_quiz_questions_and_answers(db_schema, db_rdbms, topic_list)
        return response.questions_and_answers
      except:
        pass
      pass

  def _parse_llm_response(self, response):
    json_text = re.search(r'\{.*\}', response, re.DOTALL)
    if json_text:
      return json_text
    raise ValueError('no valid JSON found')
  
  def _get_quiz_questions_and_answers(self, db_schema, db_rdbms, topic_list):
    response = self.quiz_chain.invoke({"schema": db_schema,
                                       "topics": str(topic_list),
                                       "num_questions": str(self.num_questions),
                                       "rdbms": db_rdbms})
    return response
  
  def set_prompt_template(self):
    text_template = """
You are setting an SQL quiz, with {num_questions} questions.

The database to use for questions has the following schema:
{schema}

Generate a list of {num_questions} question & answer pairs.
Each question should ask the user to write a query specific to this database, and the answer is an SQL query that is the correct solution to the question.
Questions should explicitly tell the user which columns to return, and the correct answers MUST incorpate at least one of the following SQL query topics: {topics}.
Answer queries should end in a semi-colon, and be written in one line with no breaks.

Ensure that answer queries are correct, and involve at least one of the topics given.
Queries should be written in {rdbms} syntax.

{format_instruction}

Return nothing but a valid JSON document described above.
"""
    
    prompt_template = PromptTemplate(
    input_variables=["schema", "topics", "num_questions", "rdbms"],
    template=text_template,
    partial_variables={'format_instruction': quiz_question_parser.get_format_instructions()})
    
    return prompt_template



if __name__ == "__main__":
  test_class = SQLQuizLLM(load_app_config())

  model = {'rdbms':'SQLite', 'schema': """
CREATE TABLE user (
	id INTEGER PRIMARY KEY,
	first_name TEXT NOT NULL,
	last_name TEXT NOT NULL,
	age INTEGER
);

CREATE TABLE item (
	id INTEGER PRIMARY KEY,
	name TEXT NOT NULL,
	price REAL NOT NULL
);

CREATE TABLE order (
	id INTEGER PRIMARY KEY,
	user_id INTEGER NOT NULL,
	item_id INTEGER NOT NULL,
	qty INTEGER DEFAULT 1,
	FOREIGN KEY (user_id) REFERENCES user(id),
	FOREIGN KEY (item_id) REFERENCES item(id)
);
"""}
  topics = ['EXISTS', 'NOT EXISTS', 'NOT IN', 'ANY / ALL']

  quiz = test_class.generate_quiz(model['schema'], model['rdbms'], topics)

  for q_and_a in quiz:
    print(q_and_a.quiz_question)
    print(q_and_a.correct_sql_answer)
    print()