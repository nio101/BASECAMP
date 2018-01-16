import datetime
import time
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import basecamp.tools as bc


def test_slang():
    t0 = datetime.datetime.now()
    time.sleep(2)
    t1 = datetime.datetime.now()
    assert bc.slang(t1-t0) == "2 seconds ago"
