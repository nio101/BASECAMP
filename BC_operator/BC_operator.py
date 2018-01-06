#!/usr/bin/env python3
# coding: utf-8

"""
BC_operator - handles vocal interactions and presence/absence detection
and applicable corresponding rules/actions

- depends on other services: logbook, PIR_scanner, BT_scanner
- for python3
- published under GNU GENERAL PUBLIC LICENSE (see LICENCE file)
"""

# =======================================================
# Imports

from gevent import monkey; monkey.patch_all()
import time
import requests
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


def alive_check():
    print("*** performing alive check() ***")
    t = Timer(bc.alive_frequency, alive_check)
    t.start()
    try:
        requests.get(bc.alive_url, params={'service': bc.service_name, 'version': bc.version},
                     timeout=bc.alive_timeout)
    except Exception as e:
        bc.log.error(e.__str__())
        bc.log.error("*** ERROR reaching alive_url on "+str(bc.alive_url)+" ***")
        bc.notify("ERROR", "*** ERROR reaching alive_url on "+str(bc.alive_url)+" ***")
    return


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
bc.log.info("--= Restarting =--")
bc.log.info("sleeping {} seconds for startup sync between services...".format(startup_wait))
time.sleep(startup_wait)
bc.notify("WARNING", bc.service_name+" "+bc.version+" (re)started on machine "+bc.machine_name)

# run baby, run!
alive_check()

run(host=bc.hostname, port=bc.port, server='gevent')
