#!/usr/bin/env python3
# coding: utf-8

"""
nightwatch - the last hope in case of critical failure!
             monitor the services and raise alarms if needed

features:
* receives periodical pings from services (with version details).
  if no ping is received from a given service after a given delay,
  raises an alarm and tries to reboot the machine

- depends on other services: logbook, SMS_operator, pushover_operator
- for python3
- published under GNU GENERAL PUBLIC LICENSE (see LICENCE file)
"""

# =======================================================
# Imports

from gevent import monkey; monkey.patch_all()
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

def review_alive_checks():
    """
    alive_check timestamp regular check
    """
    print("*** regular check() ***")
    t = Timer(60, review_alive_checks)
    t.start()
    now = time.time()
    for service in services:
        if (now - service_TS[service]) > max_delay:
            bc.notify("ALARM", "Service '"+service+"'' has not checked alive for a least "+str(max_delay)+" seconds!")
            bc.notify("INFO", "Will now try to reboot machine '"+service_machine[service]+"'.")
            # TODO: try to reboot the remote machine!
    return


# =======================================================
# webhooks

@get('/alive')
def do_alive():
    return(bc.version)


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
    service_TS[request.params.service] = time.time()
    service_version[request.params.service] = request.params.version
    return("OK")


# =======================================================
# main loop

# local .ini
startup_wait = bc.config.getint('startup', 'wait')
max_delay = bc.config.getint('alive_check', 'max_delay')
# also: getfloat, getint, getboolean

# read the service/machine list
# for alive_check
services = []
service_machine = {}
service_TS = {}
service_version = {}
for key in bc.config['services']:
    services.append(key)
    service_machine[key] = bc.config['services'][key]
    service_TS[key] = time.time()
    service_version[key] = "???"

# startup sync & notification
bc.log.info("--= Restarting =--")
bc.log.info("sleeping {} seconds for startup sync between services...".format(startup_wait))
time.sleep(startup_wait)
bc.notify("WARNING", bc.service_name+" "+bc.version+" (re)started on machine "+bc.machine_name)

# run baby, run!
review_alive_checks()

run(host=bc.hostname, port=bc.port, server='gevent')
