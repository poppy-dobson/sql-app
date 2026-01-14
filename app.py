import streamlit as st

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

  # for now:
  st.toast("WELL DONE")
  pass

def _check_valid_db_file(db_file):
  # for now:
  return False

def _check_topic_selection(topics):
  if len(topics) >= 3:
    return True
  return False

def button_pressed(db_file, topics):
  if _check_topic_selection(topics) and _check_valid_db_file(db_file):
    to_quiz(db_file, topics)
  elif _check_valid_db_file(db_file):
    st.toast("You must select at least 3 topics!")
  else:
    st.toast("You must upload a valid database file, try again!")

with st.sidebar:
  uploaded_db_file = st.file_uploader("Upload an sqlite3 .db file:", type=".db", key="db_upload")

  # topic selection
  topic_selection = st.multiselect("Select SQL topics to be tested on:",
                                   options=topics
                                   )

  # button to take this data and load the test page, run the model etc...
  st.button("Make me a quiz!", on_click=button_pressed, args=[uploaded_db_file, topic_selection])
