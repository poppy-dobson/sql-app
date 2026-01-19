import sqlalchemy as sqla
# import sqlite3

# ...

def check_valid_db_file(db_file):
  '''
  args:
  db_file: BytesIO of an sqlite database file

  return:
  bool: if the database input is valid / can be opened by the program
  '''
  # for now:
  return True