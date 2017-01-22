#!/usr/bin/env python
# coding: utf-8

"""
basic_zmq_service sample skeleton

(python2/python3 compatible)
"""


import logging
import logging.handlers
import configparser
import requests
# from threading import *
import umsgpack
import zmq
import time
import schedule


# =======================================================
# init
service_name = "basic_zmq_service"
# .ini
th_config = configparser.ConfigParser()
th_config.read(service_name+".ini")
logfile = th_config.get('main', 'logfile')
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

# send a restart info on pushover
r = requests.get(pushover_url, params = {'text': "le service "+service_name+" a redémarré..."})

# =======================================================
# main loop

print("ok")
