import streamlit as st

st.session_state.db_file_bytes = None
st.session_state.db_path = "temp/user_db.db"
st.session_state.topics = []
st.session_state.num_questions = 5 # in future: this should read from a config file to be manually set

from database import check_valid_db_file, write_db_bytes_to_file
from util import remove_file_if_exists

remove_file_if_exists(st.session_state.db_path)

st.title("SQL practice app :0")

st.markdown("""
Welcome :)
            
This is a project I decided to make to ~~procrastinate revising for~~ help with revising for the databases exam!
            
You can upload your own sqlite database file (.db), and an LLM will generate an SQL test, based on the topics you would like to revise,
and the specific context of your databases content (for more realistic, real-world queries!).

Pretty cool huh!

&#8592; Upload and select topics in the sidebar on the left :)
""")

topics = ["Creating Tables & Inserting Data", "Updating or Deleting Data",
          "Simple SELECT Statements", "WHERE Clause", "Simple Aggregation (MIN, MAX, AVG, COUNT, SUM)",
          "GROUP BY", "JOINs (INNER, LEFT, RIGHT, OUTER)", "Subqueries", "EXISTS / NOT EXISTS",
          "'Double NOT EXISTS'", "Creating VIEWs"]

def to_quiz(db_file, topics):
  # run quiz page
  st.switch_page("pages/quiz.py")
  pass

# def _check_valid_db_file(db_file):
#   # for now:
#   return True

def _check_topic_selection(topics):
  if len(topics) >= 3:
    return True
  return False

# def button_pressed(db_file, topics):
#   if _check_topic_selection(topics) and check_valid_db_file(db_file):
#     st.switch_page("pages/quiz.py")
#     #to_quiz(db_file, topics)
#   elif check_valid_db_file(db_file):
#     st.toast("You must select at least 3 topics!")
#   else:
#     st.toast("You must upload a valid database file, try again!")

def quiz_can_be_made(db_file, topics):
  if _check_topic_selection(topics) and check_valid_db_file(db_file):
    return True
  elif not _check_topic_selection(topics):
    st.toast("You must select at least 3 topics!")
  else:
    st.toast("You must upload a valid database file, try again!")
  
  return False

with st.sidebar:
  uploaded_db_file = st.file_uploader("Upload an sqlite3 .db file:", type=".db", key="db_upload")
  if not st.session_state.db_file_bytes and uploaded_db_file:
    st.session_state.db_file_bytes = uploaded_db_file
    write_db_bytes_to_file(st.session_state.db_file_bytes, st.session_state.db_path) # HANDLE ERRORS


  # topic selection
  topic_selection = st.multiselect("Select SQL topics to be tested on:", options=topics)
  st.session_state.topics = topic_selection

  # button to take this data and load the test page, run the model etc...
  button_clicked = st.button("Make me a quiz!", # on_click=button_pressed,
                             args=[uploaded_db_file, topic_selection])
  
  if button_clicked:
    if quiz_can_be_made(st.session_state.db_file_bytes, st.session_state.topics):
      st.switch_page("pages/quiz.py")
    else:
      st.toast("INVALID")