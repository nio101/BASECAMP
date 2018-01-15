#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
PIR scanner

dependencies: operator, logbook

(python3 compatible)
"""

from time import sleep
import logging
import logging.handlers
import configparser
import requests
import re
import sys
import socket
import time
import serial


"""
notes
=====

When pluggin the USB device creating the virtual serial port:
dmesg | grep tty
to get the device ref

then to be able to ream/write from/to /dev/ttyACM0
sudo usermod -a -G dialout $USER
+ logout/login

under ubuntu, create: sudo nano /etc/udev/rules.d/99-usb-serial.rules
to add:
SUBSYSTEM=="tty", ATTRS{idVendor}=="239a", ATTRS{idProduct}=="801f", SYMLINK+="trinketM0"
then: sudo udevadm trigger
then: ls -l /dev/trinketM0

then:
Python 3.6.3 (default, Oct  3 2017, 21:45:48)                                      
[GCC 7.2.0] on linux                     
Type "help", "copyright", "credits" or "license" for more information.             
>>> import serial   
>>> s = serial.Serial('/dev/ttyACM0')    
>>> print(s.name)   
/dev/ttyACM0        
>>> line = s.readline()                  
>>> print(line)     
b'HIT!\r\n'         
>>> s.close()
"""


# =======================================================
# helpers

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


def send_PIR_event(alias):
    try:
        requests.get(PIR_event_url, params={'alias': alias},
                     timeout=PIR_event_timeout)
    except Exception as e:
        log.error(e.__str__())
        notify("ERROR", "Error reaching operator on "+str(PIR_event_url)+" !")


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
PIR_event_url = th_config.get('PIR', 'PIR_event_url')
PIR_event_timeout = th_config.getint('PIR', 'PIR_event_timeout')
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

# MAIN -------------------------

s = serial.Serial('/dev/ttyACM0')
print(s.name)
while True:
    keyword = s.readline().decode("ASCII").rstrip()
    if keyword == "PIR1":
        print("PIR1 déclenché!")
        send_PIR_event("PIR1")
    if keyword == "PIR2":
        print("PIR2 déclenché!")
        send_PIR_event("PIR2")
s.close()
