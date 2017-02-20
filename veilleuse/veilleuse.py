#!/usr/bin/python
# encoding:utf-8


import CHIP_IO.GPIO as GPIO
from time import sleep
import logging
import logging.handlers
import configparser
import requests
import umsgpack
import zmq
import re
import sys
import socket
import CHIP_IO.Utilities as UT
UT.unexport_all()


# =======================================================
# init
service_name = re.search("([^\/]*)\.py", sys.argv[0]).group(1)
machine_name = socket.gethostname()

# .ini
th_config = configparser.ConfigParser()
th_config.read(service_name+".ini")
logfile = th_config.get('main', 'logfile')
pushover_url = th_config.get('main', 'pushover_url')
logbook_url = th_config.get('main', 'logbook_url')
thresh_low = th_config.getint('main', 'thresh_low')
thresh_high = th_config.getint('main', 'thresh_high')
influxdb_query_url = th_config.get('main', 'influxdb_query_url')
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

# ZMQ init
context = zmq.Context()
# muta PUB channel
socket_pub = context.socket(zmq.PUB)
socket_pub.connect("tcp://192.168.1.50:5000")

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

# send a restart info on pushover
# r = requests.get(pushover_url, params={'text': "le service "+service_name+" a redémarré..."})
# send a restart info to logbook
requests.get(logbook_url, params={'machine': machine_name, 'service': service_name, 'message': "redémarrage"})

while True:
    # process/evaluate the last light outdoor value every 5mn
    try:
        payload = {'db': "basecamp", 'q': "SELECT LAST(\"Lit\") FROM \"muta\" WHERE unit='jardin'"}
        r = requests.get(influxdb_query_url, params=payload)
    except requests.exceptions.RequestException as e:
        print(e.__str__())
        log.error(e.__str__())
        requests.get(logbook_url, params={'machine': machine_name, 'service': service_name, 'message': "ERREUR! problème d'accès influxdb!"})
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
                # r = requests.get(pushover_url, params={'text': "le service "+service_name+" a un problème de relais"})
                requests.get(logbook_url, params={'machine': machine_name, 'service': service_name, 'message': "ERREUR! problème relais détecté."})
                current_state = 1
            else:
                log.info("lights are OFF")
                # r = requests.get(pushover_url, params={'text': "le service "+service_name+" a éteint la veilleuse"})
                requests.get(logbook_url, params={'machine': machine_name, 'service': service_name, 'message': "extinction de la veilleuse"})
                data = umsgpack.packb([u"veilleuse", u"Il y a suffisamment de luminosité dehors, j'ai éteind la veilleuse."])
                socket_pub.send("%s %s" % ("basecamp.interphone.announce", data))
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
                # r = requests.get(pushover_url, params={'text': "le service "+service_name+" a allumé la veilleuse"})
                requests.get(logbook_url, params={'machine': machine_name, 'service': service_name, 'message': "allumage de la veilleuse"})
                data = umsgpack.packb([u"veilleuse", u"Il fait un peu trop sombre dehors, j'ai allumé la veilleuse."])
                socket_pub.send("%s %s" % ("basecamp.interphone.announce", data))
                current_state = 1
            else:
                log.error("lights are OFF, but they shouldn't be!")
                # r = requests.get(pushover_url, params={'text': "le service "+service_name+" a un problème de relais"})
                requests.get(logbook_url, params={'machine': machine_name, 'service': service_name, 'message': "ERREUR! problème relais détecté."})
                current_state = 0
    sleep(5*60)
