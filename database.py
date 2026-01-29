from sqlalchemy import create_engine, text, event
import sqlite3

def valid_sql_query(query):
  first_word = query.split()[0].upper()
  if (first_word in ['CREATE', 'INSERT', 'UPDATE', 'ALTER', 'DROP', 'DELETE', 'SELECT', 'WITH']) and (query[-1] == ';') and (query.count(';') == 1):
    return True
  return False # could be expanded to be more descriptive and tell the user what exactly was wrong with the query

class UserDatabase:
  def __init__(self, engine_string:str):
    self.engine = create_engine(engine_string, connect_args={"autocommit": False})
    self.rdbms = engine_string.split('/')[0]
    self.select_schema_query = "" # implemented in specific child classes
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
    schema = self.execute_query(self.select_schema_query)
    return schema

  def get_schema(self):
    return self.schema # (text of SQL schema statements (create table, etc))

  def execute_query(self, query):
    if valid_sql_query(query):
      query_first_command = query.split()[0].upper()
      match query_first_command:
        case "SELECT" | "WITH":
          result = self._execute_select_query(query)
        case "CREATE" | "ALTER" | "DROP":
          result = self._execute_ddl_query(query)
        case "INSERT" | "UPDATE" | "DELETE":
          result = self._execute_insert_update_delete_query(query)
      return result
    else:
      print("the query passed to execute_query was not a valid SQL answer")
      raise ValueError
    
  def _execute_select_query(self, query):
    try:
      with self.engine.connect() as conn:
        result = conn.execute(text(query)).fetchall()
      return result
    except Exception as e:
      print("failed to execute query")
      print(str(e))
      raise ValueError
    
  def _execute_insert_update_delete_query(self, query):
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

  def _execute_ddl_query(self, query):
    try:
      with self.engine.connect() as conn:
        with conn.begin() as transaction:
          conn.execute(text(query))
          schema = conn.execute(text(self.select_schema_query))
          conn.exec_driver_sql("ROLLBACK") # MIGHT USE THIS LINE
      return schema
    except Exception as e:
      print(e)
      raise ValueError
  
  def _extract_db_object_from_query(self, query):
    # not applicable to SELECT statements
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
    
    # self.sqlite_dbapi_handle_transactions()

    self.select_schema_query = "SELECT sql FROM sqlite_schema WHERE type IN ('table', 'view');"

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
    try:
      with sqlite3.connect(self.db_file_path) as conn:
        cur = conn.cursor()
        outcome = cur.execute("PRAGMA schema_version;").fetchone()
      if outcome[0] == 0:
        return False
      return True
    except Exception as e:
      print("INVALID DB")
      print(e)
      return False
  
  def get_tables(self):
    # retrieves a list of table names from the database
    tables = [row[0] for row in self.execute_query("SELECT tbl_name FROM sqlite_schema WHERE type ='table';")]
    print(tables)
    return tables

  def sqlite_engine_string(self, db_path):
    return "sqlite:///" + db_path
  
  def _execute_insert_update_delete_query(self, query):
    db_object = self._extract_db_object_from_query(query)
    try:
      with self.engine.connect() as conn:
        with conn.begin() as transaction:
          conn.execute(text(query))
          result = conn.execute(text(f"SELECT * FROM {db_object};")).fetchall() 
          conn.exec_driver_sql("ROLLBACK")
        return result
    except:
      raise ValueError

  def _execute_ddl_query(self, query):
    try:
      with self.engine.connect() as conn:
        with conn.begin() as transaction:
          conn.execute(text(query))
          schema = conn.execute(text(self.select_schema_query))
          conn.exec_driver_sql("ROLLBACK") # MIGHT USE THIS LINE
      return schema
    except Exception as e:
      print(e)
      raise ValueError
  
  def sqlite_dbapi_handle_transactions(self): # because the sqlite dbapi is stupid
    @event.listens_for(self.engine, "connect")
    def do_connect(dbapi_connection, connection_record):
      dbapi_connection.isolation_level = None

    @event.listens_for(self.engine, "begin")
    def do_begin(conn):
      conn.exec_driver_sql("BEGIN")
  

if __name__ == "__main__":
  # test here
  eng_str = "sqlite:///" + "temp/user_db.db"
  engine = create_engine(eng_str)

  @event.listens_for(engine, "connect")
  def do_connect(dbapi_connection, connection_record):
    dbapi_connection.isolation_level = None

  @event.listens_for(engine, "begin")
  def do_begin(conn):
    conn.exec_driver_sql("BEGIN")
    print("transaction begun?")

  with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM QDEL;"))
  for smth in result:
    print(smth)

  with engine.connect() as conn:
    with conn.begin() as transaction:
      conn.execute(text("DROP TABLE QDEL;"))
      conn.exec_driver_sql("ROLLBACK")

  with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM QDEL;"))
  for smth in result:
    print(smth)

  try:
    with engine.connect() as conn:
      with conn.begin() as transaction:
        conn.execute(text("DROP TABLE QDEL;"))

    with engine.connect() as conn:
      result = conn.execute(text("SELECT * FROM QDEL;"))
    for smth in result:
      print(smth)
  except Exception as e:
    print(e)

  