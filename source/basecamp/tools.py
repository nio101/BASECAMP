# tools.py

"""
basecamp.init

groups all the things common to the various scripts related initialization

- for python3
- published under GNU GENERAL PUBLIC LICENSE (see LICENCE file)
"""


import configparser
import re
import os
import sys
import socket
import requests
import logging
import logging.handlers
# import datetime


# =======================================================
# Functions

def send_to_logbook(log_type, msg):
    """
    write to remote logbook (pushover may be sent for "INFO", SMS for "ERROR" or "ALARM")
    """
    try:
        requests.get(logbook_url, params={'log_type': log_type, 'machine': machine_name, 'service': service_name, 'message': msg},
                     timeout=logbook_timeout)
    except Exception as e:
        log.error(e.__str__())
        log.error("*** ERROR reaching logbook on "+str(logbook_url)+" ***")


def notify(type, msg):
    """
    log & write to logbook, depending on the notification level
    """
    if type == "DEBUG":
        log.debug(msg)
    elif type == "INFO":
        log.info(msg)
    elif type == "WARNING":
        log.warning(msg)
        send_to_logbook(type, msg)
    elif type == "ERROR":
        log.error(msg)
        send_to_logbook(type, msg)


def slang(td):
    """
    converts timedelta to an approximate textual description
    ex.: 'a few seconds ago', 'a few minutes ago', 'an hour ago'...
    """
    if td.total_seconds() < 60:
        if int(td.total_seconds()) == 1:
            return("1 second ago")
        else:
            return("{} seconds ago".format(int(td.total_seconds())))
    elif td.total_seconds() < 3600:
        minutes = int(td.total_seconds() / 60)
        if minutes == 1:
            return("1 minute ago")
        else:
            return("{} minutes ago".format(minutes))
    elif td.total_seconds() < 24*3600:
        hours = int(td.total_seconds() / 3600)
        if hours == 1:
            return("1 hour ago")
        else:
            return("{} hours ago".format(hours))
    else:
        days = int(td.total_seconds() / 24*3600)
        if days == 1:
            return("1 day ago")
        else:
            return("{} days ago".format(days))


# =======================================================
# Init

def load_config():
    global service_name, machine_name
    global basecamp_version, service_version
    global config
    global logbook_url, logbook_timeout
    global hostname, port
    global alive_url, alive_frequency, alive_timeout

    print(os.getcwd())
    print(sys.argv[0])
    try:
        service_name = re.search("([^\/]*)\.py", sys.argv[0]).group(1)
    except:
        try:
            service_name = re.search("([^\/]*)$", sys.argv[0]).group(0)
        except:
            service_name = "(unknown)"
    print("service_name:"+service_name)
    machine_name = socket.gethostname()

    # basecamp package version
    with open('../basecamp/_version_.txt', 'r') as version_file:
        version = version_file.read()
    basecamp_version = version.rstrip("\n\r")

    # service version
    with open('_version_.txt', 'r') as version_file:
        version = version_file.read()
    service_version = version.rstrip("\n\r")

    # .ini
    config = configparser.ConfigParser()
    config.optionxform = str
    # read default config file in commons dir
    config.read_file(open("../basecamp/base_config.ini"))
    # read optional config file in local service dir
    config.read("./config.ini")
    logbook_url = config.get('logbook', 'logbook_url')
    logbook_timeout = config.getint('logbook', 'logbook_timeout')
    hostname = config.get('web_server', 'hostname')
    port = config.getint('web_server', 'port')
    alive_url = config.get('alive_check', 'url')
    alive_frequency = config.getint('alive_check', 'frequency')
    alive_timeout = config.getint('alive_check', 'http_timeout')
    # also: getfloat, getint, getboolean


def init_logs():
    global log
    # .log
    log = logging.getLogger(service_name)
    log.setLevel(logging.DEBUG)
    # create file handler
    fh = logging.handlers.RotatingFileHandler(service_name+".log", maxBytes=8000000, backupCount=5)
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

    print("*** basecamp.init ["+basecamp_version+"]: base config file loaded, version and logs initialized! ***")
