import streamlit as st

st.session_state.database = None # UserDatabase, SQLiteUserDatabase, etc object

st.session_state.db_file_bytes = None
st.session_state.db_path = "temp/user_db.db"
st.session_state.topics = []
st.session_state.num_questions = 5 # in future: this should read from a config file to be manually set

st.session_state.llm_api_key = None

# used in quiz.py, initialised here so they don't reset when the quiz page re-runs
st.session_state.quiz_question_form_elements = []
st.session_state.user_answers = []
st.session_state.quiz = None
st.session_state.submitted = False

from database import SQLiteUserDatabase # at the moment, only SQLite supported :P
from util import remove_file_if_exists
from model import verify_api_key

remove_file_if_exists(st.session_state.db_path)

st.header("SQL practice app :0")

st.markdown("""
Welcome :)
            
This is a project I decided to make to ~~procrastinate revising for~~ help with revising for the databases exam!
            
You can upload your own sqlite database file (.db), and an LLM will generate an SQL test, based on the topics you would like to revise,
and the specific context of your database's content (for more realistic, real-world queries!).

Pretty cool huh!

&#8592; Upload and select topics in the sidebar on the left :)
            
*PLEASE* don't upload any databases with personal or sensitive data, or data that you shouldn't have access too. Don't get me in trouble :(
""")

topics = ["CREATE TABLE", "CREATE VIEW", "INSERT INTO", "DELETE FROM ... WHERE", "UPDATE ... SET", "ALTER", "DROP",
          "Simple SELECT Statements", "WHERE Clause", "Simple Aggregation (MIN, MAX, AVG, COUNT, SUM)",
          "GROUP BY", "HAVING", "ORDER BY", "LIMIT", "Joins (INNER, LEFT, RIGHT, OUTER)", "Self-Joins", "Text-matching (LIKE)", "BETWEEN",
          "Subqueries, IN / NOT IN", "EXISTS / NOT EXISTS", "Nested NOT EXISTS"]


def _check_topic_selection():
  if len(st.session_state.topics) >= 3:
    return True
  return False


def quiz_can_be_made():
  try:
    if _check_topic_selection() and st.session_state.database.assert_valid_db_file() and verify_api_key(st.session_state.llm_api_key):
      return True
    elif not verify_api_key(st.session_state.llm_api_key):
      st.toast("invalid API key entered, try again!")
    elif not _check_topic_selection():
      st.toast("you must select at least 3 topics!")
    else:
      st.toast("You must upload a valid database file, try again!")
    
    return False
  except:
    return False

with st.sidebar:

  api_key = st.text_input("Enter your HF Inference API key:", type='password') # can change in the future to be for different providers, eg could be an openai api key
  if api_key:
    st.session_state.llm_api_key = api_key

  uploaded_db_file = st.file_uploader("Upload an sqlite3 .db file:", type=".db", key="db_upload")
  if uploaded_db_file and not st.session_state.database:
    try:
      st.session_state.database = SQLiteUserDatabase(uploaded_db_file)
    except Exception as e:
      st.toast("invalid database uploaded")
      st.toast(str(e))

  # topic selection
  topic_selection = st.multiselect("Select SQL topics to be tested on:", options=topics)
  st.session_state.topics = topic_selection

  # button to take this data and load the test page, run the model etc...
  button_clicked = st.button("Make me a quiz!", # on_click=button_pressed,
                             args=[uploaded_db_file, topic_selection])
  
  if button_clicked:
    if quiz_can_be_made():
      st.switch_page("pages/quiz.py")
    else:
      st.toast("error! ensure you have entered your API key, uploaded your database, and selected 3+ topics :P")