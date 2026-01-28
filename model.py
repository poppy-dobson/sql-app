import requests
import os
import re
from pydantic import BaseModel, field_validator
from typing import List
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace

from database import UserDatabase, SQLiteUserDatabase, valid_sql_query

####################################################

def verify_api_key(api_key):
  # for now, as hf is the only supported endpoint
  return _verify_hf_api_key(api_key)

def _verify_hf_api_key(api_key):
  response = requests.get('https://huggingface.co/api/whoami-v2', headers={"Authorization": f"Bearer {api_key}"})
  if response.status_code == 200:
    return True
  return False

#################

class ModelQuizQuestionOutput(BaseModel):
  quiz_question: str
  correct_sql_answer: str

  @field_validator('correct_sql_answer', mode = 'after') # THIS NEEDS TO ACTUALLY BE IMPLEMENTED THO
  @classmethod
  def validate_sql_answer(cls, query: str):
    if not valid_sql_query(query):
      raise ValueError('not a valid SQL query')
    return query

class ListOfQuizQuestions(BaseModel):
  questions_and_answers: List[ModelQuizQuestionOutput]

quiz_question_parser = PydanticOutputParser(pydantic_object=ListOfQuizQuestions)

class ModelFeedback(BaseModel):
  comments: List[str]

feedback_parser = PydanticOutputParser(pydantic_object=ModelFeedback)

class SQLQuizLLM: # overall handling of the whole process
  def __init__(self, config_dict, api_key, database: UserDatabase | SQLiteUserDatabase):
    self.config = config_dict
    self.api_key = api_key
    self.model = self.set_model()
    self.database = database

    self.quiz_prompt_template = self.set_prompt_template()
    self.feedback_prompt_template = self.set_feedback_template()
    self.improvement_msg = self.set_improvement_msg()
    self.num_questions = self.config['quiz']['num_questions']


    self.quiz_chain = self.quiz_prompt_template | self.model | self._parse_llm_response | quiz_question_parser
    self.feedback_chain = self.feedback_prompt_template | self.model | self._parse_llm_response | feedback_parser

  def set_model(self):
    if self.config['model']['endpoint'] == 'hf':
      hf_endpoint = HuggingFaceEndpoint(
      repo_id=self.config['model']['repo_id'], provider=self.config['model']['provider'],
      temperature=0.8,
      max_new_tokens=768,
      huggingfacehub_api_token=self.api_key)

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
        try:
          response = self._get_quiz_questions_and_answers(topic_list, improvement="""
                                                          Your previous attempt failed to generate a valid output. Adhere strictly to the query and formatting rules given.
                                                          """)
          return response.questions_and_answers
        except:
          print("model failed to generate valid questions and answers")
          raise RuntimeError

  def _parse_llm_response(self, response):
    json_text = re.search(r'\{.*\}', response.content, re.DOTALL)
    if json_text:
      return json_text.group(0)
    raise ValueError('no valid JSON found')
  
  def _get_quiz_questions_and_answers(self, topic_list, improvement = False):
    if not improvement:
      improvement = ""
    else:
      improvement = self.improvement_msg
    
    response = self.quiz_chain.invoke({"schema": self.database.get_schema(),
                                       "sample_data": self.database.sample_data,
                                       "topics": str(topic_list),
                                       "num_questions": str(self.num_questions),
                                       "rdbms": self.database.rdbms,
                                       "improvement": improvement})
    return response
  
  def get_quiz_answer_feedback(self, input_questions_and_answers, improvement = False):
    if not improvement:
      improvement = ""
    else:
      improvement = self.improvement_msg

    response = self.feedback_chain.invoke({"schema": self.database.get_schema(),
                                           "questions_and_answers": input_questions_and_answers,
                                           "improvement": improvement})
    return response
  
  def set_improvement_msg(self):
    return """
          Your previous attempt did not generate a valid json document within { }. Ensure the response is in this format.
          """

  def set_prompt_template(self):
    text_template = """
You are setting an SQL quiz, with {num_questions} questions.

The database to use for questions has the following schema:
{schema}

The following are examples of data in each table in the database:
{sample_data}

Generate a list of {num_questions} question & answer pairs.
Each question should ask the user to write a query specific to this database, and the answer is an SQL query that is the correct solution to the question.
All answer queries MUST involve at least one of the following SQL query topics or keywords in their functionality: {topics}.
If the answer is a SELECT statement, the question should explicitly tell the user which columns to return.
Every answer should only contain ONE SQL query.
You should use values from the example data provided, if questions require querying against specific values of columns.
Answer queries should end in a semi-colon, and be written in one line with no breaks.

Ensure that all answer queries are correct given the schema, and all involve at least one of the topics given.
Queries should be written in {rdbms} syntax.

{format_instruction}
{improvement}
Return nothing but a valid JSON document described above.
"""
    
    prompt_template = PromptTemplate(
    input_variables=["schema", "topics", "num_questions", "rdbms", "improvement"],
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
{improvement}
Return nothing but a valid JSON document described above.
"""
    prompt_template = PromptTemplate(
    input_variables=["schema", "questions_and_answers", "improvement"],
    template=text_template,
    partial_variables={'format_instruction': feedback_parser.get_format_instructions()})
    
    return prompt_template
  

############################

# testing

if __name__ == "__main__":

  def _parse_llm_response_test(response):
    json_text = re.search(r'\{.*\}', response, re.DOTALL)
    if json_text:
      return json_text.group(0)
    raise ValueError('no valid JSON found')
  
  print(_parse_llm_response_test("{test:something}"))