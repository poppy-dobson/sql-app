# the streamlit page for the 'quiz' section
import streamlit as st
from util import load_app_config

st.session_state.config = load_app_config()

from model import SQLQuizLLM

model = SQLQuizLLM(st.session_state.config, st.session_state.llm_api_key, st.session_state.database)
st.session_state.model = model

class QuizElement:
  def __init__(self, key:int, question_and_answer):
    self.key = str(key)
    self.box_key = "box_" + self.key
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

    st.divider()

  def open_to_response(self):
    st.session_state[self.key] = st.text_area("Type your answer query...", key=self.box_key)

  def set_user_answer(self, input):
    self.user_answer = input

  def get_user_answer(self):
    return self.user_answer

  def lock(self):
    self.answerable = False
    self.user_answer = st.session_state[self.box_key]

  def set_correct(self, is_correct):
    self.correct = is_correct


def execute_answer_query(query):
  try:
    result = st.session_state.database.execute_query(query)
    return result, True
  except:
    print("query failed to execute") # i'm debugging ssh
    return [], False # empty answer

def display_query_and_result(query, result_data):
  st.markdown("`" + query + "`")
  st.dataframe(data=result_data)

def quiz_submitted():
  score = 0
  incorrect_questions = []

  for i, element in enumerate(st.session_state.quiz_question_form_elements):
    st.write(f"Question {i+1}:")

    model_answer_result, valid_model_answer = execute_answer_query(element.model_answer)
    user_answer_result, valid_user_answer = execute_answer_query(element.user_answer)

    st.write("The result of your query:")
    display_query_and_result(element.user_answer, user_answer_result)
    if not valid_user_answer:
      st.write("you may not have entered a valid, executable query")

    st.write("The correct result:")
    display_query_and_result(element.model_answer, model_answer_result)
    if not valid_model_answer:
      st.write("this result might not be valid or what was requested from the llm. these models can be a bit stupid")

    # mark each question as right/wrong
    correct = valid_user_answer and ((element.model_answer.upper() == element.user_answer.upper()) or (model_answer_result == user_answer_result))

    print(f"question is {correct}")

    element.set_correct(correct)

    if element.correct:
      score += 1
    else:
      incorrect_questions.append(element)

  print(f"incorrect questions: {incorrect_questions}")

  if incorrect_questions:
    try:
      feedback = get_feedback_on_incorrect_answers(incorrect_questions).comments
      st.write(f"You got {score} question(s) right! Some feedback on your incorrect answer(s):")
      for comment in feedback:
        st.write(comment)
        st.divider()
      st.write("Please note that model responses may be incorrect, don't take it's answers as 100% correct!")
    except:
      st.write("uh oh! the llm failed to generate valid comments. sorry! hope u can spot ur mistakes anyway by looking at the answers above :P")
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
    try:
      feedback = st.session_state.model.get_quiz_answer_feedback(prompt_input)
    except:
      try:
        feedback = st.session_state.model.get_quiz_answer_feedback(prompt_input, improvement=True)
      except:
        print("valid feedback could not be generated")
        raise ValueError
  return feedback

def all_answers_have_been_entered():
  print("all_answers_been_entered_run")
  for element in st.session_state.quiz_question_form_elements:

    # debugging
    # print("user answer")
    # print(element.user_answer)
    # print("get_user_answer")
    # print(element.get_user_answer())
    #
    print(f"text box key = {st.session_state[element.box_key]}")

    if not st.session_state[element.box_key]:
      print("returned False")
      return False
  print("returned True")
  return True

def submit_pressed():
  st.session_state.submit_button_clicked = True


def display_quiz():
  with st.form("quiz1") as quiz_form:
    for element in st.session_state.quiz_question_form_elements:
      element.show()

    st.form_submit_button("Submit Answers", on_click=submit_pressed)

def validate_quiz_len(quiz):
  try:
    assert len(quiz) == st.session_state.config['quiz']['num_questions']
  except:
    print("quiz is not the right length")
    raise ValueError # is handled outside

def generate_quiz_questions():
  with st.spinner("generating quiz..."):

      try:
        quiz = st.session_state.model.generate_quiz(st.session_state.topics)
        st.session_state.quiz = quiz

        validate_quiz_len(quiz)

        return True # a valid quiz was created
      
      except:
        # more shoddy error-handling
        print("valid quiz failed to generate twice")
        return False


def main():
  print("main run")

  st.title("the quiz!")

  st.write("The database schema:")
  for table in st.session_state.database.get_schema():
    if not table[0]: continue
    table_formatted = table[0] + ';'
    st.code(table_formatted, wrap_lines=True)

  print(f"quiz={st.session_state.quiz}")
  print(f"submitted={st.session_state.submitted}")

  if (not st.session_state.quiz) and (not st.session_state.submitted):
    valid_quiz_generated = generate_quiz_questions()

    print("quiz generated")

    if not valid_quiz_generated:
      st.write("the LLM failed to generate a valid quiz. sorry! your best bet is going back to the home page and trying again :(")
    else:
      for i, question_and_answer in enumerate(st.session_state.quiz):
        st.session_state.quiz_question_form_elements.append(QuizElement((i+1), question_and_answer))

        print("added quiz questions to list")
        print(f"quiz_question_form_elements={st.session_state.quiz_question_form_elements}")


  print(f"submitted={st.session_state.submitted}")

  if 'submit_button_clicked' in st.session_state:
    print(f"submit_button_clicked={st.session_state.submit_button_clicked}")
    if st.session_state.submit_button_clicked:
      if all_answers_have_been_entered():
        for element in st.session_state.quiz_question_form_elements:
          element.lock()
    
        st.session_state.submitted = True
      else:
        st.toast("you must enter something for every question")



  if not st.session_state.submitted:
    display_quiz()
    
    print("quiz displayed")
  
  if st.session_state.submitted:
    print("button pressed, quiz submitted")

    st.toast("u submitted the quiz!")
    #st.session_state.submitted = True
    display_quiz() # should have element.answerable = False

    # debugging
    print(st.session_state.items())
    #

    quiz_submitted()
  
main()