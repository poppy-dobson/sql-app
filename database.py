import sqlalchemy as sqla
import io
from sqlalchemy import create_engine
# import sqlite3


# very pseudocod-y implementation, for now
class UserDatabase:
  def __init__(self, engine_string:str):
    self.engine = create_engine(engine_string, connect_args={"autocommit": False})
    self.schema = self._set_schema()

  def _set_schema(self):
    # execute query to get the schema
    # return schema
    pass

  def get_schema(self):
    return self.schema # (text of SQL schema statements (create table, etc))

  def execute_query(self, query):
    with self.engine.connect as conn:
      pass # ???
    # return result
    pass

class SQLiteUserDatabase(UserDatabase):
  # overrides various checking functions to have sqlite-specific functionality (eg initially opening db from file not connection str)

  def __init__(self, db_bytes, file_path = "temp/user_db.db"):
    self.db_bytes = db_bytes
    self.db_file_path = self.write_db_bytes_to_file(self.db_bytes, file_path) # this functionality is a bit weird, might change
    self.db_engine_string = self.sqlite_engine_string(self.db_file_path)

    self.engine = create_engine(self.db_engine_string, connect_args={"autocommit": False})
    self.schema = self._set_schema()

  def write_db_bytes_to_file(self, db_bytes, file_path):
    try:
      with open(file_path, "wb") as f:
        f.write(db_bytes.getbuffer())
      return file_path
    except:
      raise IOError(".db file could not be written")
  
  @classmethod # might make this not classmethod at some point
  def check_valid_sqlite_db_file(cls, db_file):
    '''
    args:
    db_file: path to an sqlite database file

    return:
    bool: if the database input is valid / can be opened by the program
    '''
    # for now:
    return True
  
  def assert_valid_db_file(self):
    return SQLiteUserDatabase.check_valid_sqlite_db_file(self.db_file_path)

  #@classmethod # function grouped with the class but doesn't need an instance :)
  def sqlite_engine_string(self, db_path):
    return "sqlite:///" + db_path