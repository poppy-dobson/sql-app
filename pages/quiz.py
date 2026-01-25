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

    st.write("Question " + self.key + ":")
    st.write(self.question)
    self.open_to_response()

    # for debugging
    st.write(self.model_answer)

    st.divider()

  def open_to_response(self):
    self.user_answer = st.text_area("Type your answer query...", key=self.key)

  def get_user_answer(self):
    return self.user_answer

  def lock(self):
    self.answerable = False

  def set_correct(self, is_correct):
    self.correct = is_correct

st.title("the quiz!")

# here, before the form, will display the user's schema from the database object!
st.write("The database schema:")
for table in st.session_state.database.get_schema():
  if not table[0]: continue
  table_formatted = table[0] + ';'
  st.code(table_formatted, wrap_lines=True)

def mark_question(model_answer, user_answer):
  if model_answer == user_answer:
    return True
  else:
    model_answer_result = st.session_state.database.execute_query(model_answer)
    try:
      user_answer_result = st.session_state.database.execute_query(user_answer)
    except Exception as e: # make this more specific and return a specific error message
      print("the user query failed to execute") # temp error handling
      return False
  
  if model_answer_result == user_answer_result:
    return True
  return False

def _quiz_submitted():
  score = 0
  incorrect_questions = []
  for element in st.session_state.quiz_question_form_elements:
    user_answer = element.get_user_answer()
    element.lock()
    st.session_state.user_answers.append(user_answer)

    # mark each question as right/wrong
    correct = mark_question(element.model_answer, element.get_user_answer())

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
    
  feedback = st.session_state.model.get_quiz_answer_feedback(prompt_input)
  return feedback

def show_results():
  # not implemented yet
  pass

# shoddy debugging
print(st.session_state.quiz)
print(st.session_state.submitted)

if (not st.session_state.quiz) and (not st.session_state.submitted):
  with st.spinner("generating quiz..."):

    print("generating quiz")

    try:
      quiz = st.session_state.model.generate_quiz(st.session_state.topics)
      st.session_state.quiz = quiz

      print("quiz made")
      print(st.session_state.quiz)

      try:
        assert len(quiz) == config['quiz']['num_questions']
      except:
        print("quiz is not the right length")
    except:
      # temporary lazy error handling
      print("quiz failed to generate")

def submit_pressed():
  st.session_state.submitted = True

if not st.session_state.submitted:
  with st.form("quiz1") as quiz_form:
    print("form generated") # debugging
    for i, question_and_answer in enumerate(st.session_state.quiz):
      st.session_state.quiz_question_form_elements.append(QuizElement(str(i+1), question_and_answer))

    #submitted = st.form_submit_button("Submit Answers")
    st.form_submit_button("Submit Answers", on_click=submit_pressed)

if st.session_state.submitted:

  print("button pressed, quiz submitted")
  print(st.session_state.submitted)

  st.toast("u submitted the quiz!")
  #st.session_state.submitted = True
  _quiz_submitted()


  