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


# =======================================================
# init
service_name = "veilleuse"

# .ini
th_config = configparser.ConfigParser()
th_config.read(service_name+".ini")
logfile = th_config.get('main', 'logfile')
pushover_url = th_config.get('main', 'pushover_url')
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
r = requests.get(pushover_url, params={'text': "le service "+service_name+" a redémarré..."})

while True:
    # check the last light outdoor value every 5mn
    payload = {'db': "basecamp", 'q': "SELECT LAST(\"Lit\") FROM \"muta\" WHERE unit='jardin'"}
    r = requests.get(influxdb_query_url, params=payload)
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
            r = requests.get(pushover_url, params={'text': "le service "+service_name+" a un problème"})
            current_state = 1
        else:
            log.info("lights are OFF")
            r = requests.get(pushover_url, params={'text': "le service "+service_name+" a éteint la veilleuse"})
            data = umsgpack.packb([u"veilleuse", u"Le jour est levé, j'ai éteind la veilleuse."])
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
            r = requests.get(pushover_url, params={'text': "le service "+service_name+" a allumé la veilleuse"})
            data = umsgpack.packb([u"veilleuse", u"La nuit est tombée, j'ai allumé la veilleuse."])
            socket_pub.send("%s %s" % ("basecamp.interphone.announce", data))
            current_state = 1
        else:
            log.error("lights are OFF, but they shouldn't be!")
            r = requests.get(pushover_url, params={'text': "le service "+service_name+" a un problème"})
            current_state = 0
    sleep(5*60)
