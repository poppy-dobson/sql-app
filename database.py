from sqlalchemy import create_engine, text
# import sqlite3

def valid_sql_query(query):
  first_word = query.split()[0].upper()
  if (first_word in ['CREATE', 'INSERT', 'UPDATE', 'ALTER', 'DROP', 'DELETE', 'SELECT', 'WITH']) and query[-1] == ';':
    if query.count(';') == 1:
      return True
  return False

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
    if valid_sql_query(query):
      query_first_command = query.split()[0].upper()
      if query_first_command in ("SELECT", "WITH"): # WITH for CTEs and stuff
        result = self.execute_select_query(query)
      else:
        try:
          result = self._execute_not_select(query)
          return result
        except:
          raise ValueError
    else:
      print("the query passed to execute_query was not a valid SQL answer")
      raise ValueError
    
  def execute_select_query(self, query):
    try:
      with self.engine.connect() as conn:
        result = conn.execute(text(query)).fetchall()
      return result
    except Exception as e:
      print("failed to execute query")
      print(str(e))
      raise ValueError
    
  def execute_insert_update_delete_query(self, query):
    db_object = self._extract_db_object_from_query(query)
    try:
      with self.engine.connect() as conn:
        with conn.begin() as transaction: # for sqlite this matters less as the file is a copy of the user's database, however for databases with connections the app shouldn't edit any of their data
          conn.execute(text(query))
          result = conn.execute(text(f"SELECT * FROM {db_object};")).fetchall() # could to self.execute_query but this might break cause it's a conn within a conn
          transaction.rollback() # undo any changes made, ensure they are NOT committed :O
        return result
    except:
      raise ValueError

  def execute_ddl_query(self, query):
    ...
    schema = self._set_schema()
    return schema
    
  # def _execute_not_select(self, query):
  #   operation = query.split()[0].upper()
  #   db_object = self._extract_db_object_from_query(query)

  #   try:
  #     with self.engine.connect() as conn:
  #       with conn.begin() as transaction: # for sqlite this matters less as the file is a copy of the user's database, however for databases with connections the app shouldn't edit any of their data
          
  #         match operation:
  #           case "CREATE" | "ALTER" | "DROP":
  #             conn.execute(text(query))
  #             result = [(query,)] # update this to get the schema instead
            
  #           case "INSERT" | "UPDATE" | "DELETE":
  #             conn.execute(text(query))
  #             result = conn.execute(text(f"SELECT * FROM {db_object};")).fetchall() # could to self.execute_query but this might break cause it's a conn within a conn
            
  #           case _:
  #             print("query could not be executed")
  #             result = None
  #         transaction.rollback() # undo any changes made, ensure they are NOT committed :O
      
  #     # debugging
  #     print(result)
  #     #

  #     return result
  #   except:
  #     raise ValueError
  
  def _extract_db_object_from_query(self, query):
    words = query.upper().split()
    for word in words:
      if word not in ("CREATE", "INSERT", "UPDATE", "ALTER", "DROP", "DELETE") and word not in ("TABLE", "VIEW") and word not in ("FROM", "INTO"):
        return word
    return None

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
    schema = self.execute_query("SELECT sql FROM sqlite_schema WHERE type IN ('table', 'view');")
    return schema

  def sqlite_engine_string(self, db_path):
    return "sqlite:///" + db_path
  

if __name__ == "__main__":
  # test here
  eng = create_engine("sqlite:///" + "temp/user_db.db")
  with eng.connect() as conn:
    result = conn.execute(text("""SELECT tbl_name FROM sqlite_schema WHERE type ='table';""")).fetchall()
  print(result)