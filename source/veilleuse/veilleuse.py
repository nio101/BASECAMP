#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
veilleuse service

dependencies: interphone, logbook

(python3)
"""

import CHIP_IO.GPIO as GPIO
from time import sleep
import logging
import logging.handlers
import configparser
import requests
import re
import sys
import socket
import time
import CHIP_IO.Utilities as UT
UT.unexport_all()


# =======================================================
# helpers

def send_to_logbook(log_type, msg):
    try:
        requests.get(logbook_url, params={'log_type': log_type, 'machine': machine_name, 'service': service_name, 'message': msg},
                     timeout=logbook_timeout)
    except Exception as e:
        log.error(e.__str__())
        log.error("*** ERROR reaching logbook on "+str(logbook_url)+" ***")


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
thresh_low = th_config.getint('main', 'thresh_low')
thresh_high = th_config.getint('main', 'thresh_high')
influxdb_query_url = th_config.get('main', 'influxdb_query_url')
interphone_url = th_config.get('main', 'interphone_url')
wait_at_startup = th_config.getint('main', 'wait_at_startup')
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

# brings an error! :(
# GPIO.cleanup()

probe = "CSID0"
set = "CSID2"
reset = "CSID4"
GPIO.setup(set, GPIO.OUT)
GPIO.output(set, 0)
GPIO.setup(reset, GPIO.OUT)
GPIO.output(reset, 0)
GPIO.setup(probe, GPIO.IN)
if GPIO.input(probe):
    log.info("lights are ON")
    current_state = 1
else:
    log.info("lights are OFF")
    current_state = 0

# send a restart info to logbook
send_to_logbook("WARNING", "Restarting...")

while True:
    # process/evaluate the last light outdoor value every 5mn
    try:
        payload = {'db': "basecamp", 'q': "SELECT LAST(\"Lit\") FROM \"muta\" WHERE unit='jardin'"}
        r = requests.get(influxdb_query_url, params=payload)
    except requests.exceptions.RequestException as e:
        log.error(e.__str__())
        send_to_logbook("ERROR", "Can't reach InfluxDB!")
    else:
        res = r.json()["results"][0]["series"][0]["values"][0]
        light_value = res[1]
        log.info("light_value: %i" % light_value)
        if (current_state == 1) and (light_value > thresh_high):
            log.info("turning lights OFF")
            GPIO.output(reset, 1)
            sleep(0.02)
            GPIO.output(reset, 0)
            # check it!
            if GPIO.input(probe):
                log.error("lights are ON, but they shouldn't be!")
                send_to_logbook("ERROR", "Relay problem: lights are ON, but they shouldn't be!")
                current_state = 1
            else:
                log.info("lights are OFF")
                send_to_logbook("INFO", "Extinction de la veilleuse de nuit.")
                try:
                    requests.get(interphone_url, params={'service': service_name, 'announce': "Nico, le jour s'est levé... Bonne journée!"})
                except:
                    send_to_logbook("ERROR", "Can't reach interphone on "+interphone_url)
                current_state = 0
        elif (current_state == 0) and (light_value < thresh_low):
            # lights should be ON
            log.info("turning lights ON")
            GPIO.output(set, 1)
            sleep(0.02)
            GPIO.output(set, 0)
            # check it!
            if GPIO.input(probe):
                log.info("lights are ON")
                send_to_logbook("INFO", "Allumage de la veilleuse de nuit.")
                try:
                    requests.get(interphone_url, params={'service': service_name, 'announce': "Nico, La nuit est tombée... Bonne soirée!"})
                except:
                    send_to_logbook("ERROR", "Can't reach interphone on "+interphone_url)
                current_state = 1
            else:
                log.error("lights are OFF, but they shouldn't be!")
                send_to_logbook("ERROR", "Relay problem: lights are OFF, but they shouldn't be!")
                current_state = 0
    sleep(5*60)
