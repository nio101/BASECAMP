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


# =======================================================
# webhooks

@get('/alive')
def do_alive():
    return(tools.service_version)


@get('/turn_mellotron_on')
def turn_mellotron_on():
    print("YES!!! :)")
    return("OK")


# =======================================================
# main loop

if __name__ == "__main__":
    # initialize config/logs
    tools.load_config(optional_service_name="alexa_interface")
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
    # alive_check()
    run(host=tools.hostname, port=tools.port, server='gevent')
