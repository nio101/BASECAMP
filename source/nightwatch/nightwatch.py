#!/usr/bin/env python3
# coding: utf-8

"""
nightwatch - the last hope in case of critical failure!
             monitor the services and raise alarms if needed

features:
* receives periodical pings from services (with version details).
  if no ping is received from a given service after a given delay,
  raises an alarm (and tries to reboot the machine?)

- depends on other services: logbook, SMS_operator, pushover_operator
- for python3
- published under GNU GENERAL PUBLIC LICENSE (see LICENCE file)
"""

# =======================================================
# Imports

from gevent import monkey; monkey.patch_all()
import time
import datetime
from bottle import run, request, get
from threading import Timer

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import basecamp.tools as tools
import basecamp.db as db


# =======================================================
# helpers

def review_alive_checks():
    """
    alive_check timestamp regular check
    """
    tools.log.info("*** alive check() review ***")
    t = Timer(alive_review_frequency, review_alive_checks)
    t.start()
    now = datetime.datetime.now()
    for service in services:
        if (now - service_TS[service]).total_seconds() > max_delay:
            tools.notify("ALARM", "Service '"+service+"'' has not checked alive for "+tools.slang(now - service_TS[service]))
            # bc.notify("INFO", "Will now try to reboot machine '"+service_machine[service]+"'.")
            # TODO: try to reboot the remote machine?
            # !!! do not reboot the same machine multiple times, establish a list of rebooting machines or reset timers for services on the same machine
    return


# =======================================================
# webhooks

@get('/alive')
def do_alive():
    return(tools.service_name+" "+tools.service_version)


@get('/alive_check')
def do_alive_check():
    global services_TS
    global services_version
    if request.params.service == "":
        return("ERROR: service param is missing!")
    if request.params.version == "":
        return("ERROR: version param is missing!")
    if request.params.service not in services:
        return("ERROR: service value is unknown!")
    service_TS[request.params.service] = datetime.datetime.now()
    service_version[request.params.service] = request.params.version
    return("OK")


@get('/status')
def do_status():
    status = {}
    status['alive_check'] = []
    now = datetime.datetime.now()
    for service in services:
        status['alive_check'].append({'service': service, 'version': service_version[service], 'last_seen_ts': service_TS[service].strftime("%A %d %B %H:%M:%S"),
                                      'last_seen_slang': tools.slang(now - service_TS[service])})
    return(status)


# =======================================================
# main loop

if __name__ == "__main__":
    # initialize config/logs
    tools.load_config(optional_service_name="nightwatch")
    # .ini
    startup_wait = tools.config.getint('startup', 'wait')
    max_delay = tools.config.getint('alive_check', 'max_delay')
    alive_review_frequency = tools.config.getint('alive_check', 'review_frequency')
    # also: getfloat, getint, getboolean
    tools.init_logs()
    influx_json_body = db.init()
    # startup sync & notification
    tools.log.info("--= Restarting =--")
    tools.log.info("sleeping {} seconds for startup sync between services...".format(startup_wait))
    time.sleep(startup_wait)
    # read & init the service/machine list
    # for alive_check
    services = []
    service_machine = {}
    service_TS = {}
    service_version = {}
    for key in tools.config['services']:
        services.append(key)
        service_machine[key] = tools.config['services'][key]
        service_TS[key] = datetime.datetime.now()
        service_version[key] = "???"
    tools.notify("WARNING", tools.service_version+" - (re)started!")
    # alive_check()
    run(host=tools.hostname, port=tools.port, server='gevent')
