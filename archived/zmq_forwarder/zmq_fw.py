#! /usr/bin/env python
# -*- coding: utf8 -*-

"""
ZMQ multiple PUB/SUB port forwarder

logs to '/var/tmp/muta.log'.

code is coming from:
https://learning-0mq-with-pyzmq.readthedocs.org/en/latest/pyzmq/devices/forwarder.html
"""

import logging
import logging.handlers
import configparser
import zmq
import re
import sys
import socket
import requests


pub_port = sys.argv[1]
sub_port = sys.argv[2]

service_name = re.search("([^\/]*)\.py", sys.argv[0]).group(1)
machine_name = socket.gethostname()

# .ini
th_config = configparser.ConfigParser()
th_config.read(service_name+".ini")
logfile = th_config.get('main', 'logfile')
logbook_url = th_config.get('main', 'logbook_url')

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
# send a restart info to logbook
requests.get(logbook_url, params={'machine': machine_name, 'service': service_name, 'message': "redémarrage"})

try:
    context = zmq.Context(1)
    # Socket facing PUBs
    frontend = context.socket(zmq.SUB)
    frontend.bind("tcp://*:%s" % pub_port)
    frontend.setsockopt(zmq.SUBSCRIBE, "")
    # Socket facing SUBs
    backend = context.socket(zmq.PUB)
    backend.bind("tcp://*:%s" % sub_port)
    log.info("ready: from PUB on %s to SUB on port %s" % (pub_port, sub_port))
    zmq.device(zmq.FORWARDER, frontend, backend)
except Exception, e:
    print(e.__str__())
    log.error(e.__str__())
    requests.get(logbook_url, params={'machine': machine_name, 'service': service_name, 'message': "ERREUR! arrêt du service"})
finally:
    pass
frontend.close()
backend.close()
context.term()
