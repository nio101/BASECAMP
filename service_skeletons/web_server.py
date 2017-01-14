#!/usr/bin/env python
# coding: utf-8

"""
Basecamp pushover notification service

(python2/python3 compatible)
note:   webserver may not be multi-threaded/non-blocking.
        if needed, use bottle with gunicorn for example.
"""


from bottle import run, request, get
import time
import logging
import logging.handlers
import configparser
import errno
import zmq
import umsgpack
from threading import Timer
import requests


# =======================================================
# init

# .ini
th_config = configparser.ConfigParser()
th_config.read("pushover_operator.ini")
logfile = th_config.get('main', 'logfile')
hostname = th_config.get('main', 'hostname')
app_token = th_config.get('main', 'app_token')
user_token = th_config.get('main', 'user_token')
# also: getfloat, getint, getboolean

# log
log = logging.getLogger('basecamp_UI')
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

log.warning("pushover_operator is (re)starting !")

# =======================================================
# timers

shutdown = False

def check_XYZ():
    t1 = Timer(4.0, check_XYZ)
    t1.start()
    log.info("timer function run")
    if shutdown:
        t1.cancel()

# =======================================================
# URL handlers

@get('/alive')
def do_alive():
    return "OK"


@get('/send_pushover_notification')
def do_TTS():
    uni_text = request.query.text
    log.info("sending notification:%s"%uni_text)
    r = requests.post('https://api.pushover.net/1/messages.json', data = {'token':app_token, 'user':user_token, 'message':uni_text})
    if r.status_code==200 and r.json()["status"]==1:
        return "OK"
    else:
        return "ERROR"

# =======================================================
# main loop

# start timer functions
t1 = Timer(4.0, check_XYZ)
t1.start()

run(host=hostname, port=80)

shutdown = True
# let the timer thread shutdown
t1.join()
