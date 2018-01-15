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

from gevent import monkey; monkey.patch_all()
import time
from bottle import run, request, get, response
from json import dumps
from subprocess import check_output
from threading import Timer

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import basecamp.tools as bc
import basecamp.influxDB as db


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

if __name__ == "__main__":
    # initialize config/logs
    bc.load_config()
    bc.init_logs()
    # .ini
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
    bc.notify("WARNING", bc.service_version+" - (re)started!")
    # run baby, run!
    regular_check()
    run(host=bc.hostname, port=bc.port, server='gevent')
