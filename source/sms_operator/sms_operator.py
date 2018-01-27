#!/usr/bin/env python2
# coding: utf-8

"""
sms_operator

dependencies: GSM modem with SIM card + gammu + python-gammu, logbook

! should be python3 compatible, but the service frequently looses connectivity with the modem !

That doesn't seem to happen with python2, so let's stick to python2.x version.

"""


from bottle import run, request, get
import logging
import logging.handlers
import configparser
import requests
import gammu
from threading import Timer
import re
import sys
import socket
import time


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
hostname = th_config.get('main', 'hostname')
port = th_config.getint('main', 'port')
allowed_msisdn = map(lambda s: s.strip('\''), th_config.get('main', 'allowed_msisdn').split(','))
gammu_config_filename = th_config.get('main', 'gammu_config_filename')
logbook_url = th_config.get('main', 'logbook_url')
logbook_timeout = th_config.getint('main', 'logbook_timeout')
wait_at_startup = th_config.getint('main', 'wait_at_startup')
max_failed_SMS_checks = th_config.getint('main', 'max_failed_SMS_checks')
# also: getfloat, getint, getboolean

# log
log = logging.getLogger(service_name)
log.setLevel(logging.DEBUG)
# create file handler
fh = logging.handlers.RotatingFileHandler(logfile, maxBytes=8000000, backupCount=5)
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

# Create state machine object
sm = gammu.StateMachine()
# Read ~/.gammurc
sm.ReadConfig(Filename=gammu_config_filename)
# Connect to phone
try:
    sm.Init()
except Exception as e:
    print(e.__str__())
    log.error(e)
    log.error("Erreur init GAMMU, sm.Init() failed")
    # write an error to logbook, but without SMS_forwarding, to prevent a loop!
    exit(1)
# Reads network information from phone
netinfo = sm.GetNetworkInfo()
# Print information
network_code = netinfo['NetworkCode']
if (network_code != '208 01') and (network_code != '208 02'):
    log.error("no registered mobile network, network code:'%s'" % network_code)
    # Don't write an ERROR to logbook! would create an infinite loop!
    exit(1)
signal_level = sm.GetSignalQuality()['SignalPercent']
if (signal_level < 30):
    log.warning("mobile network signal level is LOW: %i" % signal_level)
    send_to_logbook("WARNING", "Mobile network signal level is LOW: "+str(signal_level))
else:
    log.info("mobile network signal level is: %i" % signal_level)
    send_to_logbook("INFO", "Mobile network signal level: "+str(signal_level))
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

# =======================================================
# URL handlers


@get('/alive')
def do_alive():
    return "OK"


@get('/send_SMS')
def send_SMS():
    msisdn = request.query.msisdn
    uni_text = request.query.text
    log.info("sending SMS to %s: '%s'" % (msisdn, uni_text))
    message = {'Text': uni_text, 'SMSC': {'Location': 1}, 'Number': msisdn}
    try:
        sm.SendSMS(message)
        send_to_logbook("INFO", "SMS envoyé à "+str(msisdn))
        log.info("SMS sent!")
        return("OK")
    except Exception as e:
        print(e.__str__())
        log.error(e)
        log.error("error sending SMS to %s: '%s'" % (msisdn, uni_text))
        # Don't write an ERROR to logbook! would create an infinite loop!
        return("ERROR")


@get('/signal_level')
def get_signal_level():
    level = sm.GetSignalQuality()
    # return({status: "OK", "GSM_signal_level": level})
    return(level)


# =======================================================
# incoming SMS check timer function

def check_incoming_SMS():
    global consecutive_check_failures
    global last_try_OK
    try:
        status = sm.GetSMSStatus()
        last_try_OK = True
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
                gammu.DecodeSMS(x)
                m = x[0]
                log.info("new SMS received from %s: %s" % (m['Number'], m['Text']))
                send_to_logbook("INFO", "SMS received from "+str(m['Number']))
                if (m['Number'] in allowed_msisdn):
                    # TODO: exploiter les SMS en arrivée
                    pass
                else:
                    log.warning("%s is not allowed to send SMS to Basecamp!" % m['Number'])
                    send_to_logbook("WARNING", str(m['Number'])+" not authorized to send SMS to BASECAMP!")
                # now delete it
                sm.DeleteSMS(0, m['Location'])
    except Exception as e:
        print(e.__str__())
        log.error(e)
        log.warning("could not check incoming SMS! :s")
        if last_try_OK is not True:
            consecutive_check_failures = consecutive_check_failures + 1
            if consecutive_check_failures == max_failed_SMS_checks:
                send_to_logbook("WARNING", "Could'nt check incoming SMS - "+str(max_failed_SMS_checks)+" times in a row!")
                consecutive_check_failures = 0
        else:
            last_try_OK = False
    t = Timer(10.0, check_incoming_SMS)
    t.start()


# =======================================================
# main loop

consecutive_check_failures = 0
last_try_OK = True
t = Timer(10.0, check_incoming_SMS)
t.start()
run(host=hostname, port=port)
