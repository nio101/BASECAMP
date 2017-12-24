#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
scheduler service

dependencies: logbook, interphone
"""

import logging
import logging.handlers
import configparser
import requests
import time
import schedule
import re
import sys
import socket


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
# send a restart info to logbook
send_to_logbook("WARNING", "Restarting...")


# =======================================================
# time announce job

def job(h, m):
    # ajouter des conditions:
    if (m == "00"):
        announce = "Nico! Il est déjà "+h+"h!"
    else:
        announce = "Nico! Il est déjà "+h+"h"+m+"!"
    requests.get(interphone_url, params={'service': service_name, 'announce': announce})


# =======================================================
# main stuff

hours = []
# announce only between 7h00-22h30
for hour in range(7, 23):
    hours.append('{0:01d}'.format(hour))
# hour_marks = ["00", "15", "30", "45"]
hour_marks = ["00", "30"]
for hour in hours:
    for mn in hour_marks:
        schedule.every().day.at(hour+":"+mn).do(job, hour, mn)
"""
schedule.every(10).seconds.do(job)
schedule.every().hour.do(job)
schedule.every().day.at("10:30").do(job)
schedule.every().monday.do(job)
schedule.every().wednesday.at("13:15").do(job)
"""
# time.sleep(10)
# schedule.run_all(delay_seconds=2)

while True:
    schedule.run_pending()
    time.sleep(2)
