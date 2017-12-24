#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
interphone service

dependencies: logbook, TTS server

(python2.7/python3 compatible)
"""

import logging
import logging.handlers
import configparser
import requests
import os
from subprocess import call, check_output
import re
import sys
import socket
from datetime import datetime
from bottle import run, request, get
import uuid
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


def download_file(url):
    # local_filename = url.split('/')[-1]
    local_filename = "last_announce.wav"
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
    return local_filename

# =======================================================
# HTTP requests


@get('/alive')
def do_alive():
    return "OK"


@get('/lock')
def do_lock():
    global key
    global key_ts
    global key_service
    if request.query.service == "":
        return("ERROR: must provide a service name/id")
    now = datetime.now()
    if ((now-key_ts).total_seconds() > keys_lifespan):
        key = ""
    if (key == ""):
        key = uuid.uuid4().hex
        key_ts = datetime.now()
        key_service = request.query.service
        result = {'key': key}
        log.info("%s: key=%s" % (key_service, key))
        return(result)
    else:
        return("ERROR: interphone already locked by service "+key_service)


@get('/release')
def do_release():
    global key
    global key_ts
    global key_service
    if request.query.service == "":
        return("ERROR: must provide a service name/id")
    if request.query.service != key_service:
        return("ERROR: service name/id doesn't match")
    key = ""
    key_service = ""
    log.info("%s: key released" % (key_service))
    return("OK")


@get('/announce')
def do_set_profile():
    global key
    service = request.query.service
    announce = request.query.announce
    m_key = request.query.key
    volume = request.query.volume
    if volume == "":
        volume = default_volume

    log.info("%s (key=%s): %s (%s)" % (service, m_key, announce, volume))

    now = datetime.now()
    if ((now-key_ts).total_seconds() > keys_lifespan):
        key = ""
    if (m_key != key):
        return("ERROR: key is missing, or invalid/expired")

    # request TTS wav file
    r = requests.get(tts_url, params={'text': announce}, stream=True)
    if r.status_code == 200:
        wav_url = r.text
        # download wav file
        local_wav = download_file(wav_url)
        # call(["sox", local_wav, "announce_plus_contrast.wav", "contrast"])
        # play wav file
        # volume = 70
        # call(["amixer", "-D", "pulse", "sset", "Master", str(volume)+"%"])
        """
        if (now.hour >= 7) and (now.hour <= 23):
            vol1 = "50%"
        else:
            vol1 = "35%"
        """
        # post-process the synthesis
        # call(["sox", local_wav, "announce_plus_contrast.wav", "contrast"])
        # apply multiple high pass filters on voice
        call(["sox", local_wav, "tmp.wav", "contrast", "highpass", "1000", "highpass", "1000", "gain", "15"])
        # concatenate with in and out fx
        call(["sox", "fx/beep_in_22k.wav", "tmp.wav", "fx/beep_out_22k.wav", "tmp2.wav", "gain", "3"])
        # mix with static noise and trim
        res1 = check_output(["soxi", "-D", "tmp2.wav"])
        print(res1)
        print("'"+str(float(res1))+"'")
        call(["sox", "-m", "tmp2.wav", "fx/static_22k.wav", "res.wav", "trim", "0", str(float(res1))])
        # now, play it
        print("'"+volume+"'")
        call(["amixer", "-D", "pulse", "sset", "Master", volume])
        # os.system("aplay codeccall.wav")
        # os.system("aplay codecopen.wav")
        os.system("aplay res.wav")
        # os.system("aplay codecover.wav")
        # remove the file
        os.remove(local_wav)
        return("OK")
    else:
        send_to_logbook("ERROR", "ERROR getting the TTS file from "+tts_url)
        return("ERROR getting the TTS file from "+tts_url)


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
tts_url = th_config.get('main', 'tts_url')
wait_at_startup = th_config.getint('main', 'wait_at_startup')
keys_lifespan = th_config.getint('http', 'lifespan')
hostname = th_config.get('http', 'hostname')
port = th_config.getint('http', 'port')
default_volume = th_config.get('main', 'default_volume')
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
# main stuff
key = ""
key_ts = datetime.now()
key_service = ""
run(host=hostname, port=port)
