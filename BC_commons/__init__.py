# __init.py__

"""
BC_commons

groups all the things common to the various scripts

- for python3
- published under GNU GENERAL PUBLIC LICENSE (see LICENCE file)
"""


import configparser
import re
import sys
import socket
import requests
import logging
import logging.handlers


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


# =======================================================
# Init

service_name = re.search("([^\/]*)\.py", sys.argv[0]).group(1)
machine_name = socket.gethostname()

# version
with open('_version_.txt', 'r') as version_file:
    version = version_file.read()
version = version.rstrip("\n\r")

# .ini
config = configparser.ConfigParser()
config.optionxform = str
# read default config file in commons dir
config.read_file(open("../BC_commons/base_config.ini"))
# read optional config file in local service dir
config.read(service_name+".ini")
logbook_url = config.get('logbook', 'logbook_url')
logbook_timeout = config.getint('logbook', 'logbook_timeout')
hostname = config.get('web_server', 'hostname')
port = config.getint('web_server', 'port')
alive_url = config.get('alive_check', 'url')
alive_frequency = config.getint('alive_check', 'frequency')
alive_timeout = config.getint('alive_check', 'http_timeout')
# also: getfloat, getint, getboolean

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

print("*** BC_commons: base config file loaded, version and logs initialized! ***")
