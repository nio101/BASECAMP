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
from bottle import run, request, get
from subprocess import check_output
from threading import Timer

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import basecamp.tools as tools
import basecamp.db as db


# =======================================================
# helpers

class PreMode:   # reflects the current presence mode
    COCOON, ASLEEP, LOCKOUT = range(3)


def alive_check():
    tools.log.info("*** performing alive check() ***")
    t = Timer(tools.alive_frequency, alive_check)
    t.start()
    try:
        requests.get(tools.alive_url, params={'service': tools.service_name, 'version': tools.service_version},
                     timeout=tools.alive_timeout)
    except Exception as e:
        tools.log.error(e.__str__())
        tools.log.error("*** ERROR reaching alive_url on "+str(tools.alive_url)+" ***")
        tools.notify("ERROR", "*** ERROR reaching alive_url on "+str(tools.alive_url)+" ***")
    return


# =======================================================
# webhooks

@get('/alive')
def do_alive():
    return(tools.service_version)


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

if __name__ == "__main__":
    # initialize config/logs
    tools.load_config(optional_service_name="operator")
    # .ini
    startup_wait = tools.config.getint('startup', 'wait')
    # also: getfloat, getint, getboolean
    tools.init_logs()
    influx_json_body = db.init()
    # startup sync & notification
    tools.log.info("--= Restarting =--")
    tools.log.info("sleeping {} seconds for startup sync between services...".format(startup_wait))
    time.sleep(startup_wait)
    tools.notify("WARNING", tools.service_version+" - (re)started!")
    alive_check()
    run(host=tools.hostname, port=tools.port, server='gevent')
