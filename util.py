import os

def remove_file_if_exists(path):
  try:
    os.remove(path)
  except:
    pass