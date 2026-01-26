# the streamlit page for the 'quiz' section
import streamlit as st
from util import load_app_config

config = load_app_config()

from database import UserDatabase, SQLiteUserDatabase
from model import SQLQuizLLM

model = SQLQuizLLM(config, st.session_state.database)
st.session_state.model = model

class QuizElement:
  def __init__(self, key:str, question_and_answer):
    self.key = key
    self.question = question_and_answer.quiz_question
    self.model_answer = question_and_answer.correct_sql_answer
    self.answerable = True
    self.correct = None

  def show(self):
    st.write("Question " + self.key + ":")
    st.write(self.question)
    if self.answerable:
      self.open_to_response()
    else:
      st.write("Your answer:")
      try: st.markdown("`" + self.user_answer + "`")
      except: pass # lazy error handling - will fix

    # for debugging
    # st.write(self.model_answer)
    #

    st.divider()

  def open_to_response(self):
    self.user_answer = st.text_area("Type your answer query...", key=self.key)

  def get_user_answer(self):
    return self.user_answer

  def lock(self):
    self.answerable = False

  def set_correct(self, is_correct):
    self.correct = is_correct


def execute_answer_query(query):
  try:
    result = st.session_state.database.execute_query(query)
    return result
  except:
    print("query failed to execute") # i'm debugging
    #raise RuntimeError
    return []

def quiz_submitted():
  score = 0
  incorrect_questions = []

  for i, element in enumerate(st.session_state.quiz_question_form_elements):
    st.write(f"Question {i+1}:")

    model_answer_result = execute_answer_query(element.model_answer)
    user_answer_result = execute_answer_query(element.user_answer)

    st.write("The result of your query:")
    st.dataframe(data=user_answer_result)

    st.write("The correct result:")
    st.write(element.model_answer)
    st.dataframe(model_answer_result)

    # mark each question as right/wrong
    correct = (element.model_answer.upper() == element.user_answer.upper()) or (model_answer_result == user_answer_result)

    print(f"question is {correct}")

    element.set_correct(correct)

    if element.correct:
      score += 1
    else:
      incorrect_questions.append(element)

  print(f"incorrect questions: {incorrect_questions}")

  if incorrect_questions:
    feedback = get_feedback_on_incorrect_answers(incorrect_questions).comments
    st.write(f"You got {score} question(s) right! Some feedback on your incorrect answer(s):")
    for comment in feedback:
      st.write(comment)
      st.divider()
  else:
    st.write("You got every question right! Well Done!")


def get_feedback_on_incorrect_answers(incorrect_questions):
  prompt_input = ""
  for element in incorrect_questions:
    prompt_input = prompt_input + f"""
Question: {element.question}

Model Answer (correct): {element.model_answer}

User Answer (incorrect): {element.get_user_answer()}

"""
  with st.spinner("getting feedback on incorrect results..."):
    feedback = st.session_state.model.get_quiz_answer_feedback(prompt_input)
  return feedback

def all_answers_have_been_entered():
  for element in st.session_state.quiz_question_form_elements:
    if not element.user_answer:
      return False
  return True

def submit_pressed():
  if all_answers_have_been_entered():
    for element in st.session_state.quiz_question_form_elements:
      element.lock()
    
    st.session_state.submitted = True
  else:
    st.toast("you must enter something for every question")


def display_quiz():
  with st.form("quiz1") as quiz_form:
    for element in st.session_state.quiz_question_form_elements:
      element.show()

    #submitted = st.form_submit_button("Submit Answers")
    st.form_submit_button("Submit Answers", on_click=submit_pressed)

def generate_quiz_questions():
  with st.spinner("generating quiz..."):

      try:
        quiz = st.session_state.model.generate_quiz(st.session_state.topics)
        st.session_state.quiz = quiz

        print("quiz made")
        print(st.session_state.quiz)

        for i, question_and_answer in enumerate(st.session_state.quiz):
          st.session_state.quiz_question_form_elements.append(QuizElement(str(i+1), question_and_answer))

        try:
          assert len(quiz) == config['quiz']['num_questions']
        except:
          print("quiz is not the right length")
      except:
        # temporary lazy error handling
        print("quiz failed to generate")


def main():
  st.title("the quiz!")

  st.write("The database schema:")
  for table in st.session_state.database.get_schema():
    if not table[0]: continue
    table_formatted = table[0] + ';'
    st.code(table_formatted, wrap_lines=True)

  if (not st.session_state.quiz) and (not st.session_state.submitted):
    generate_quiz_questions()

  if not st.session_state.submitted:
    display_quiz()
  
  if st.session_state.submitted:
    print("button pressed, quiz submitted")

    st.toast("u submitted the quiz!")
    #st.session_state.submitted = True
    display_quiz() # should have element.answerable = False
    quiz_submitted()
  
main()