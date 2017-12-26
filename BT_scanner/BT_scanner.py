#!/usr/bin/env python3
# coding: utf-8

"""
BT_scanner service

- depends on: logbook, hcitool+l2ping on host
- for python3
- published under GNU GENERAL PUBLIC LICENSE (see LICENCE file)
"""

import logging
import logging.handlers
import configparser
import requests
import time
from bottle import run, request, get
import re
import sys
import socket
from bottle import response
from json import dumps
import subprocess


# =======================================================
# helpers

def send_to_logbook(log_type, msg):
    try:
        requests.get(logbook_url, params={'log_type': log_type, 'machine': machine_name, 'service': service_name, 'message': msg},
                     timeout=logbook_timeout)
    except Exception as e:
        log.error(e.__str__())
        log.error("*** ERROR reaching logbook on "+str(logbook_url)+" ***")


def notify(msg):
    """
    proper notification tryout
    """
    log.info(msg)
    send_to_logbook("INFO", msg)


def scan_alias(alias):
    """
    BT scan on given address
    """
    # do a hcitool connect+rssi or a l2ping?
    # do the quickest! rssi is optional, presence is vital
    p = subprocess.Popen(["scp -r "], shell=True)
    sts = p.wait()
    print(sts)
    result = "FOUND"
    rssi = -75
    return(result, rssi)


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
# init

service_name = re.search("([^\/]*)\.py", sys.argv[0]).group(1)
machine_name = socket.gethostname()

# .ini
th_config = configparser.ConfigParser()
th_config.read(service_name+".ini")
logfile = th_config.get('main', 'logfile')
logbook_url = th_config.get('main', 'logbook_url')
logbook_timeout = th_config.getint('main', 'logbook_timeout')
hostname = th_config.get('main', 'hostname')
port = th_config.getint('main', 'port')
wait_at_startup = th_config.getint('main', 'wait_at_startup')
# also: getfloat, getint, getboolean
# read the aliases & BT_addresses
BT_aliases = {}
for key in th_config['BT']:
    BT_aliases[key] = th_config['BT'][key]

# log
log = logging.getLogger(service_name)
log.setLevel(logging.DEBUG)
# create file handler
fh = logging.handlers.RotatingFileHandler(
              logfile, maxBytes=8000000, backupCount=5)
fh.setLevel(logging.DEBUG)
# create console hangler with higher level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - [%(name)s] %(levelname)s: %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
log.addHandler(fh)
log.addHandler(ch)

time.sleep(wait_at_startup)

log.warning(service_name+" restarted")
# send a restart info to logbook
send_to_logbook("WARNING", "Restarting...")


# =======================================================
# main loop

run(host=hostname, port=port)
