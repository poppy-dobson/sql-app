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
from database import UserDatabase, SQLiteUserDatabase

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
    if (first_word not in ['CREATE', 'INSERT', 'UPDATE', 'ALTER', 'DROP', 'DELETE', 'SELECT', 'WITH']) or query[-1] != ';':
      raise ValueError('not a valid SQL query')
    return query

class ListOfQuizQuestions(BaseModel):
  questions_and_answers: List[ModelQuizQuestionOutput]

quiz_question_parser = PydanticOutputParser(pydantic_object=ListOfQuizQuestions)

class ModelFeedback(BaseModel):
  comments: List[str]

feedback_parser = PydanticOutputParser(pydantic_object=ModelFeedback)

class SQLQuizLLM: # overall handling of the whole process
  def __init__(self, config_dict, database: UserDatabase | SQLiteUserDatabase):
    self.config = config_dict
    self.model = self.set_model()
    self.database = database

    self.quiz_prompt_template = self.set_prompt_template()
    self.feedback_prompt_template = self.set_feedback_template()
    self.num_questions = self.config['quiz']['num_questions']


    self.quiz_chain = self.quiz_prompt_template | self.model | quiz_question_parser
    self.feedback_chain = self.feedback_prompt_template | self.model | feedback_parser

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

  def generate_quiz(self, topic_list):
    valid_quiz = False
    while not valid_quiz:
      try:
        response = self._get_quiz_questions_and_answers(topic_list)
        return response.questions_and_answers
      except:
        pass
      pass

  # def _parse_llm_response(self, response):
  #   json_text = re.search(r'\{.*\}', response, re.DOTALL)
  #   if json_text:
  #     return json_text
  #   raise ValueError('no valid JSON found')
  
  def _get_quiz_questions_and_answers(self, topic_list):
    response = self.quiz_chain.invoke({"schema": self.database.get_schema(),
                                       "sample_data": self.database.sample_data,
                                       "topics": str(topic_list),
                                       "num_questions": str(self.num_questions),
                                       "rdbms": self.database.rdbms})
    return response
  
  def get_quiz_answer_feedback(self, input_questions_and_answers):
    response = self.feedback_chain.invoke({"schema": self.database.get_schema(),
                                           "questions_and_answers": input_questions_and_answers})
    return response
  
  def set_prompt_template(self):
    text_template = """
You are setting an SQL quiz, with {num_questions} questions.

The database to use for questions has the following schema:
{schema}

The following are examples of data in each table in the database:
{sample_data}

Generate a list of {num_questions} question & answer pairs.
Each question should ask the user to write a query specific to this database, and the answer is an SQL query that is the correct solution to the question.
All answers MUST incorpate at least one of the following SQL query topics or keywords: {topics}.
If the answer is a SELECT statement, the question should explicitly tell the user which columns to return. If the answer is a CREATE, INSERT, UPDATE, ALTER, DROP or DELETE statement, this should be the only statement given in the answer.
You should use values from the example data provided, if questions require querying against specific values of columns.
Answer queries should end in a semi-colon, and be written in one line with no breaks.

Ensure that all answer queries are correct given the schema, and all involve at least one of the topics given.
Queries should be written in {rdbms} syntax.

{format_instruction}

Return nothing but a valid JSON document described above.
"""
    
    prompt_template = PromptTemplate(
    input_variables=["schema", "topics", "num_questions", "rdbms"],
    template=text_template,
    partial_variables={'format_instruction': quiz_question_parser.get_format_instructions()})
    
    return prompt_template
  
  def set_feedback_template(self):
    text_template = """
You are marking an SQL quiz. Generate a list of text comments in response to the user's incorrect answers.

The database used in the questions has the following schema:
{schema}

For each of the following question(s) that the user answered incorrectly, respond with the reason why the model answer is correct, and the user's answer is incorrect:
{questions_and_answers}


{format_instruction}

Return nothing but a valid JSON document described above.
"""
    prompt_template = PromptTemplate(
    input_variables=["schema", "questions_and_answers"],
    template=text_template,
    partial_variables={'format_instruction': feedback_parser.get_format_instructions()})
    
    return prompt_template