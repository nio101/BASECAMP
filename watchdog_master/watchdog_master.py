#!/usr/bin/env python
# coding: utf-8

"""
watchdog_master

dependencies: all other modules! :s

(python2/python3 compatible)
"""


import logging
import logging.handlers
import configparser
import requests
# from threading import *
import zmq
import time
import schedule
import socket
import sys
import re
try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error importing RPi.GPIO!  This is probably because you need superuser privileges. \
    You can achieve this by using 'sudo' to run your script.")
    exit(1)


# =======================================================


class T_power_status:   # reflects the current power state
    NORMAL, OUTAGE = range(2)


# =======================================================
# init
service_name = re.search("([^\/]*)\.py", sys.argv[0]).group(1)
machine_name = socket.gethostname()
# .ini
th_config = configparser.ConfigParser()
th_config.read(service_name+".ini")
logfile = th_config.get('main', 'logfile')
logbook_url = th_config.get('main', 'logbook_url')
wait_at_startup = th_config.getint('main', 'wait_at_startup')
# also: getfloat, getint, getboolean

# log
log = logging.getLogger(service_name)
log.setLevel(logging.DEBUG)
# create file handler
fh = logging.handlers.RotatingFileHandler(
              logfile, maxBytes=8000000, backupCount=5)
fh.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - [%(name)s] %(levelname)s: %(message)s')
fh.setFormatter(formatter)
# add the handlers to the logger
log.addHandler(fh)

log.warning(service_name+" is (re)starting !")
time.sleep(wait_at_startup)

# ZMQ init
context = zmq.Context()
# muta PUB channel
socket_pub = context.socket(zmq.PUB)
socket_pub.connect("tcp://bc-hq.local:5000")
log.info("ZMQ connect: PUB on tcp://bc-hq.local:5000")
# muta SUB channel
socket_sub = context.socket(zmq.SUB)
socket_sub.connect("tcp://127.0.0.1:5001")
topicfilter = "basecamp.interphone.announce"
socket_sub.setsockopt(zmq.SUBSCRIBE, topicfilter)
log.debug("ZMQ connect: SUB on tcp://127.0.0.1:5001")
# give ZMQ some time to setup the channels
time.sleep(1)
poller = zmq.Poller()
poller.register(socket_sub, zmq.POLLIN)

# GPIO init
GPIO.setmode(GPIO.BOARD)

# probe: pin #15, GPIO22
# set/reset: pins #16/18, GPIO 24/23
probe = 15
set = 16
reset = 18
GPIO.setup(probe, GPIO.IN)
GPIO.setup(set, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(reset, GPIO.OUT, initial=GPIO.LOW)
# shut down the heater,
# check with probe
log.info("resetting the heater relay")
GPIO.output(reset, 1)
time.sleep(0.02)
GPIO.output(reset, 0)
if GPIO.input(probe):
    log.info("relay probe is HIGH")
    # alarm if probe is not 0
    log.error("unable to reset heater relay, stopping here")
    requests.get(logbook_url, params={'machine': machine_name, 'service': service_name, 'message': "ERREUR! impossible d'ouvrir le relais!"})
    exit(1)
else:
    log.info("relay probe is LOW")
    log.info("heater latching relay is OFF")
relay_out = 0

# send a restart info on pushover
# requests.get(pushover_url, params = {'text': "le service "+service_name+" a redémarré..."})
requests.get(logbook_url, params={'machine': machine_name, 'service': service_name, 'message': "le service a redémarré!"})

# =======================================================
# main loop

m_power_status = T_power_status.NORMAL

print("let's go")

# tester présence courant/secteur

# tester liaison rpc vers supervisord
# tester services/applicatifs
# tester ZMQ
