#!/usr/bin/env python
# coding: utf-8

"""
Basecamp pushover notification service

(python2/python3 compatible)
note:   webserver may not be multi-threaded/non-blocking.
        if needed, use bottle with gunicorn for example.
"""


from bottle import run, request, get
import logging
import logging.handlers
import configparser
import requests


# =======================================================
# init
service_name = "pushover_operator"

# .ini
th_config = configparser.ConfigParser()
th_config.read(service_name+".ini")
logfile = th_config.get('main', 'logfile')
hostname = th_config.get('main', 'hostname')
port = th_config.getint('main', 'port')
app_token = th_config.get('main', 'app_token')
user_token = th_config.get('main', 'user_token')
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

# send a restart info on pushover
r = requests.post('https://api.pushover.net/1/messages.json', data = {'token':app_token, 'user':user_token, 'message':"le service "+service_name+" a redémarré..."})

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

run(host=hostname, port=port)
