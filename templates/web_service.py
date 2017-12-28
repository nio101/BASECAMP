#!/usr/bin/env python3
# coding: utf-8

"""
Template for a basic BASECAMP service with a web_server+timer

- depends on other services: logbook
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
# BASECAMP_commons import
from inspect import getsourcefile
import os.path
current_dir = os.path.dirname(os.path.abspath(getsourcefile(lambda: 0)))
sys.path.insert(0, current_dir[:current_dir.rfind(os.path.sep)])
import BASECAMP_commons as bc
from BASECAMP_commons import influxDB
sys.path.pop(0)  # remove parent dir from sys.path


# =======================================================
# helpers

class ThMode:   # ThMode reflects the current heating mode
    ECO, COMFORT = range(2)


def scan_alias(alias):
    """
    bla bla bla
    """
    try:
        res = check_output(["sudo hcitool cc "+BT_aliases[alias]+" && sudo hcitool rssi "+BT_aliases[alias]], shell=True)
        result = res.splitlines()[-1].decode('ascii')
        rssi = -75
    except Exception as e:
        bc.notify("ERROR", "Error trying to scan alias "+alias+": "+e.__str__())
        result = "NOT FOUND"
        rssi = -99
    return(result, rssi)


def regular_check():
    print("*** regular check() ***")
    t = Timer(5.0, regular_check)
    t.start()
    return


# =======================================================
# webhooks

@get('/alive')
def do_alive():
    return "OK"


@get('/scan_all')
def do_scan_all():
    res = []
    for alias in BT_aliases:
        (result, rssi) = scan_alias(alias)
        res.append({'alias': alias, 'result': result, 'rssi': str(rssi)})
    response.content_type = 'application/json'
    return dumps(res)


@get('/scan')
def do_scan():
    if request.params.alias != "":
        if request.params.alias in BT_aliases:
            (result, rssi) = scan_alias(request.params.alias)
            return({'alias': request.params.alias, 'result': result, 'rssi': str(rssi)})
        else:
            return("ERROR: alias unknown!")
    else:
        return("ERROR: alias field not found!")


# =======================================================
# main loop

# after that, you can use ThMode.ECO or ThMode.COMFORT as values for variables

# .ini
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
regular_check()

if bc.workers == 1:
    run(host=bc.hostname, port=bc.port)
else:
    run(host=bc.hostname, port=bc.port, server="gunicorn", workers=bc.workers)
