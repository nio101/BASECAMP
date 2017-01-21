#!/usr/bin/env python
# coding: utf-8

"""
Basecamp web_server sample skeleton

(python2/python3 compatible)
note:   webserver may not be multi-threaded/non-blocking.
        if needed, use bottle with gunicorn for example.
"""


from bottle import run, request, get
import logging
import logging.handlers
import configparser
import requests
import gammu
from threading import *
import umsgpack
import zmq


# =======================================================
# init
service_name = "SMS_operator"
# .ini
th_config = configparser.ConfigParser()
th_config.read(service_name+".ini")
logfile = th_config.get('main', 'logfile')
hostname = th_config.get('main', 'hostname')
port = th_config.getint('main', 'port')
allowed_msisdn = map(lambda s: s.strip('\''), th_config.get('main', 'allowed_msisdn').split(','))
pushover_url = th_config.get('main', 'pushover_url')
gammu_config_filename = th_config.get('main', 'gammu_config_filename')
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
# muta orders channel
socket_pub = context.socket(zmq.PUB)
socket_pub.connect("tcp://bc-hq.local:5000")
log.info("ZMQ connect: PUB on tcp://bc-hq.local:5000 (orders)")

# Create state machine object
sm = gammu.StateMachine()
# Read ~/.gammurc
sm.ReadConfig(Filename = gammu_config_filename)
# Connect to phone
sm.Init()
# Reads network information from phone
netinfo = sm.GetNetworkInfo()
# Print information
network_code = netinfo['NetworkCode']
if (network_code != '208 01') and (network_code != '208 02'):
    log.error("no registered mobile network, network code:'%s'" % network_code)
    exit(1)
signal_level = sm.GetSignalQuality()['SignalPercent']
if (signal_level < 30):
    log.error("mobile network signal level is LOW: %i" % signal_level)
# check for any existing SMS, and purge them if needed
status = sm.GetSMSStatus()
remain = status['SIMUsed'] + status['PhoneUsed'] + status['TemplatesUsed']
if (remain > 0):
    log.warning("%i SMS will now be deleted" % remain)
    sms = []
    start = True
    while remain > 0:
        if start:
            cursms = sm.GetNextSMS(Start=True, Folder=0)
            start = False
        else:
            cursms = sm.GetNextSMS(Location=cursms[0]['Location'], Folder=0)
        remain = remain - len(cursms)
        sms.append(cursms)
    data = gammu.LinkSMS(sms)
    for x in data:
        v = gammu.DecodeSMS(x)
        m = x[0]
        sm.DeleteSMS(0, m['Location'])

# send a restart info on pushover
r = requests.get(pushover_url, params = {'text': "le service "+service_name+" a redémarré..."})

# =======================================================
# URL handlers

@get('/alive')
def do_alive():
    return "OK"


@get('/send_SMS')
def do_TTS():
    msisdn = request.query.msisdn
    uni_text = request.query.text
    log.info("sending SMS to %s: '%s'" % (msisdn, uni_text))
    message = {'Text': uni_text, 'SMSC': {'Location': 1}, 'Number': msisdn}
    try:
        sm.SendSMS(message)
        return("OK")
    except:
        log.error("error sending SMS to %s: '%s'" % (msisdn, uni_text))
        return("ERROR")

# =======================================================
# incoming SMS check timer function

def check_incoming_SMS():
    try:
        status = sm.GetSMSStatus()
        remain = status['SIMUsed'] + status['PhoneUsed'] + status['TemplatesUsed']
        if (remain > 0):
            sms = []
            start = True
            while remain > 0:
                if start:
                    cursms = sm.GetNextSMS(Start=True, Folder=0)
                    start = False
                else:
                    cursms = sm.GetNextSMS(Location=cursms[0]['Location'], Folder=0)
                remain = remain - len(cursms)
                sms.append(cursms)
            data = gammu.LinkSMS(sms)
            for x in data:
                v = gammu.DecodeSMS(x)
                m = x[0]
                log.info("new SMS received from %s: %s" % (m['Number'], m['Text']))
                if (m['Number'] in allowed_msisdn):
                    # broadcast info to Basecamp PUB
                    msg_data = umsgpack.packb([m['Number'], m['Text']])
                    topic = "basecamp.SMS.incoming"
                    socket_pub.send("%s %s" % (topic, msg_data))
                else:
                    log.warning("%s is not allowed to send SMS to Basecamp!" % m['Number'])
                # now delete it
                sm.DeleteSMS(0, m['Location'])
    except:
        log.warning("could not check incoming SMS! :s")
    t = Timer(10.0, check_incoming_SMS)
    t.start()

# =======================================================
# main loop

t = Timer(10.0, check_incoming_SMS)
t.start()
run(host=hostname, port=port)
