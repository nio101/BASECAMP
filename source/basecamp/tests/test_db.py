import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

print(os.getcwd())
# os.chdir("..")
# print(os.getcwd())

# import basecamp.tools as bc
import basecamp.db as db


# content of test_sample.py
def func(x):
    return x + 1


def test_answer():
    assert func(4) == 5
