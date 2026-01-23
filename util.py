import os
import tomllib

def remove_file_if_exists(path):
  try:
    os.remove(path)
  except:
    pass

def load_app_config(path="app_config.toml"):
  with open(path, "rb") as config_file:
    config = tomllib.load(config_file)
  return config