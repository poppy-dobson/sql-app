import pytest

class TestModel:
  @pytest.fixture(scope="class")
  def model():
    # temp
    return None
  pass

class TestDB:
  pass

class TestSQLiteDB:
  pass

def test_test():
  assert 1 == 1