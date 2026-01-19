# the streamlit page for the 'quiz' section
import streamlit as st

# from database import ...
# from model import ...

st.session_state.quiz_question_form_elements = []

class QuizQuestionFormElement:
  def __init__(self, key:str):
    self.key = key
    self.answerable = True
    self.correct = None

    st.write("Question " + self.key + ":")
    st.write("[model's question]")
    self.open_to_response()
    st.divider()

  def open_to_response(self):
    self.user_answer = st.text_area("Type your answer query...", key=self.key)

  def get_user_answer(self):
    return self.user_answer

  def lock(self):
    self.answerable = False

  def set_correct(self, is_correct):
    self.correct = is_correct

# ...
st.title("the quiz!")


# here, before the form, will display the user's schema from the database object!
# st.write(...)

def _quiz_submitted():
  for element in st.session_state.quiz_question_form_elements:
    # get user response
    # element.get_user_answer()
    element.lock()

    # mark each question as right/wrong

    # element.set_correct(...)
  
  # the answers should be sent off to the database to query
  pass

with st.form("quiz1") as quiz_form:
  for i in range(1, 6):
    st.session_state.quiz_question_form_elements.append(QuizQuestionFormElement(str(i)))

  submitted = st.form_submit_button("Submit Answers")
  if submitted:
    st.toast("u submitted!")
    _quiz_submitted()