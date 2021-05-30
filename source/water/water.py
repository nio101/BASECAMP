#!/usr/bin/env python3
# coding: utf-8

"""
water monitoring service

detect impulses and immediatly send events to influxdb
one impulse == 1 liter

dependencies: wifi, logbook, influxdb

for python3 (for python2, don't use the readline() str/ascii conversion)
<insert open source licence here>
"""

import logging
import logging.handlers
import configparser
import requests
import time
import datetime
from influxdb import InfluxDBClient
import re
import sys
import socket
import os
from threading import Timer


# sudo apt-get -y install python3-rpi.gpio
try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error importing RPi.GPIO!  This is probably because you need superuser privileges.  You can achieve this by using 'sudo' to run your script")
    exit(1)


# =======================================================
# helpers

def send_to_logbook(log_type, msg):
    try:
        requests.get(logbook_url, params={'log_type': log_type, 'machine': machine_name, 'service': service_name, 'message': msg},
                     timeout=logbook_timeout)
    except Exception as e:
        log.error(e.__str__())
        log.error("*** ERROR reaching logbook on "+str(logbook_url)+" ***")


def export_metrics():
    """
    export the average values of metrics to influxdb
    and resets the values
    """
    global liter_count
    log.debug("... time to export metrics to influxdb!")
    if (liter_count > 0):
        log.info("liter_count = %i" % (liter_count))
        influx_json_body[0]['time'] = datetime.datetime.utcnow().isoformat()
        influx_json_body[0]['fields'] = {'water': liter_count}
        log.info("writing to influxdb: "+str(influx_json_body))
        try:
            client.write_points(influx_json_body)
        except Exception as e:
            log.error(e.__str__())
            log.error("Error reaching infludb on "+str(influxdb_host)+":"+str(influxdb_port))
            send_to_logbook("ERROR", "Cannot write to InfluxDB!")
        liter_count = 0
    else:
        log.warning("nothing to export.")
    t = Timer(30.0, export_metrics)
    t.start()


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
wait_at_startup = th_config.getint('main', 'wait_at_startup')
influxdb_host = th_config.get("influxdb", "influxdb_host")
influxdb_port = th_config.get("influxdb", "influxdb_port")
# also: getfloat, getint, getboolean

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

log.warning(service_name+" is (re)starting !")
time.sleep(wait_at_startup)
send_to_logbook("WARNING", "Restarting...")

# influxdb init
client = InfluxDBClient(influxdb_host, influxdb_port)
client.switch_database('basecamp')
log.info("influxdb will be contacted on "+str(influxdb_host)+":"+str(influxdb_port))
influx_json_body = [
    {
        "measurement": "water",
        "tags": {},
        "time": "",
        "fields": {}
    }
]

# OS: highest priority
# os.nice(-20)

# GPIO init
GPIO.setmode(GPIO.BOARD)

# GPIO
# probe: pin #11, GPIO17

probe = 11
GPIO.setup(probe, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# =======================================================
# main loop

liter_count = 0

t = Timer(30.0, export_metrics)
t.start()

while True:
    while not GPIO.input(probe):
        time.sleep(0.01)
    while GPIO.input(probe):
        time.sleep(0.01)
    # an impulse has been detected
    log.info("1l impulse detected.")
    liter_count = liter_count + 1
