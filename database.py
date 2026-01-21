import sqlalchemy as sqla
import io
from sqlalchemy import create_engine
# import sqlite3

# ...

def write_db_bytes_to_file(db_bytes, file_path = "temp/user_db.db"):
  # ADD ERROR HANDLING!
  with open(file_path, "wb") as f:
    f.write(db_bytes.getbuffer())

def check_valid_db_file(db_file):
  '''
  args:
  db_bytes: BytesIO of an sqlite database file

  return:
  bool: if the database input is valid / can be opened by the program
  '''
  # for now:
  return True

def sqlite_engine_string(db_path):
  return "sqlite:///" + db_path

# very pseudocod-y implementation, for now
class DataBaseInteraction:
  def __init__(self, engine_string:str):
    self.engine = create_engine(engine_string, connect_args={"autocommit": False})
    self.schema = self._set_schema()
    pass

  def _set_schema(self):
    # execute query to get the schema
    # return schema
    pass

  def get_schema(self):
    # return self.schema (text of SQL schema statements (create table, etc))
    pass

  def execute_query(self, query):
    with self.engine.connect as conn:
      pass # ???
    # return result
    pass