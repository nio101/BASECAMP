#!/usr/bin/env python3
# coding: utf-8

"""
operator - handles vocal interactions and presence/absence detection
and applicable corresponding rules/actions

- depends on other services: logbook, PIR_scanner, BT_scanner
- for python3
- published under GNU GENERAL PUBLIC LICENSE (see LICENCE file)
"""

# =======================================================
# Imports

import time
from bottle import run, request, get, response
import sys
from json import dumps
from subprocess import check_output
from threading import Timer
# BC_commons import
from inspect import getsourcefile
import os.path
current_dir = os.path.dirname(os.path.abspath(getsourcefile(lambda: 0)))
sys.path.insert(0, current_dir[:current_dir.rfind(os.path.sep)])
import BC_commons as bc
from BC_commons import influxDB
sys.path.pop(0)  # remove parent dir from sys.path


# =======================================================
# helpers

class PreMode:   # reflects the current presence mode
    COCOON, ASLEEP, LOCKOUT = range(3)


"""
def regular_check():
    print("*** regular check() ***")
    t = Timer(5.0, regular_check)
    t.start()
    return
"""


# =======================================================
# webhooks

@get('/alive')
def do_alive():
    return(bc.version)


@get('/PIR_event')
def do_PIR_event():
    if request.params.alias == "":
        return("ERROR: alias param is missing!")
    elif request.params.alias == "PIR2":
        # PIR1 is for front screen UI detection
        # force the display on
        try:
            res = check_output(["sh -c \'export DISPLAY=:0; xset dpms force on\'"], shell=True)
        except:
            return("ERROR trying to set display on! "+res)
    elif request.params.alias == "PIR1":
        pass
    return("OK")


# =======================================================
# main loop

# after that, you can use ThMode.ECO or ThMode.COMFORT as values for variables

# local .ini
startup_wait = bc.config.getint('startup', 'wait')
# also: getfloat, getint, getboolean
# read the aliases & BT_addresses
BT_aliases = {}
for key in bc.config['BT']:
    BT_aliases[key] = bc.config['BT'][key]

# startup sync & notification
print("sleeping {} seconds for startup sync between services...".format(startup_wait))
time.sleep(startup_wait)
bc.notify("WARNING", "has restarted!")

# run baby, run!
# regular_check()

if bc.workers == 1:
    run(host=bc.hostname, port=bc.port)
else:
    run(host=bc.hostname, port=bc.port, server="gunicorn", workers=bc.workers)
