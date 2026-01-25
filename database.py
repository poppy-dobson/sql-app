import sqlalchemy as sqla
import io
from sqlalchemy import create_engine, text
# import sqlite3


class UserDatabase:
  def __init__(self, engine_string:str):
    self.engine = create_engine(engine_string, connect_args={"autocommit": False})
    self.rdbms = engine_string.split('/')[0]
    self.schema = self._set_schema()
    self.tables = self.get_tables()
    self.assert_db_contains_enough_data()
    self.sample_data = self.get_sample_rows()

  def get_sample_rows(self):
    sample_rows = {}
    for table in self.tables:
      rows = self.execute_query(f"SELECT * FROM {table} LIMIT 3;")
      sample_rows[table] = rows
    return sample_rows

  def assert_db_contains_enough_data(self):
    if len(self.tables) < 3:
      raise ValueError("database doesn't contain enough tables (3 minimum)")
    for table in self.tables:
      num_rows = self.execute_query(f"SELECT COUNT(*) FROM {table};")[0][0]
      if num_rows < 4:
        raise ValueError("a table doesn't contain enough rows of data (4 minimum)")

  def get_tables(self):
    # retrieves a list of table names from the database
    tables = self.execute_query("[query to list the tables in the database]")
    # FIX THE FUNCTIONALITY
    return tables

  def _set_schema(self):
    # execute query to get the schema
    # return schema
    pass

  def get_schema(self):
    return self.schema # (text of SQL schema statements (create table, etc))

  def execute_query(self, query):
    try:
      with self.engine.connect() as conn:
        result = conn.execute(text(query)).fetchall()
      return result
    except Exception as e:
      print("failed to execute query")
      print(str(e))
      # raise ...

class SQLiteUserDatabase(UserDatabase):
  # overrides various checking functions to have sqlite-specific functionality (eg initially opening db from file not connection str)

  def __init__(self, db_bytes, file_path = "temp/user_db.db"):
    self.db_bytes = db_bytes
    self.db_file_path = self.write_db_bytes_to_file(self.db_bytes, file_path) # this functionality is a bit weird, might change
    self.rdbms = "SQLite"

    self.assert_valid_db_file()

    self.db_engine_string = self.sqlite_engine_string(self.db_file_path)
    self.engine = create_engine(self.db_engine_string)

    self.schema = self._set_schema()
    self.tables = self.get_tables()

    self.assert_db_contains_enough_data()

    self.sample_data = self.get_sample_rows()
    

  def write_db_bytes_to_file(self, db_bytes, file_path):
    try:
      with open(file_path, "wb") as f:
        f.write(db_bytes.getbuffer())
      return file_path
    except:
      raise IOError(".db file could not be written")
  
  def assert_valid_db_file(self):
    # for now:
    return True
  
  def get_tables(self):
    # retrieves a list of table names from the database
    tables = [row[0] for row in self.execute_query("SELECT tbl_name FROM sqlite_schema WHERE type ='table';")]
    print(tables)
    return tables
  
  def _set_schema(self):
    schema = self.execute_query("SELECT sql FROM sqlite_schema;")
    return schema

  #@classmethod # function grouped with the class but doesn't need an instance :)
  def sqlite_engine_string(self, db_path):
    return "sqlite:///" + db_path
  

if __name__ == "__main__":
  # test here
  eng = create_engine("sqlite:///" + "temp/user_db.db")
  with eng.connect() as conn:
    result = conn.execute(text("SELECT tbl_name FROM sqlite_schema WHERE type ='table';")).fetchall()
  print(result)