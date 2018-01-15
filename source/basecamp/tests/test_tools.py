import datetime
import time
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

print(os.getcwd())
# os.chdir("..")
# print(os.getcwd())

import basecamp.tools as bc
# import tools as bc


# content of test_sample.py
def func(x):
    return x + 1


def test_answer():
    assert func(4) == 5


def test_slang():
    t0 = datetime.datetime.now()
    time.sleep(2)
    t1 = datetime.datetime.now()
    assert bc.slang(t1-t0) == "2 seconds ago"
