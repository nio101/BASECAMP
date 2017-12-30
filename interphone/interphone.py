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


def update_ini():
    """
    to save the value of interphone_enabled & default_volume
    """
    global th_config
    th_config.set("main", "default_volume", str(default_volume))
    if announces_enabled:
        th_config.set("main", "announces_enabled", "true")
    else:
        th_config.set("main", "announces_enabled", "false")

    with open(service_name+".ini", 'w') as configfile:
        th_config.write(configfile)
    return


def radio_speech(announce, volume):
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
        return True
    else:
        send_to_logbook("ERROR", "ERROR getting the TTS file from "+tts_url)
        return False


# =======================================================
# HTTP requests

@get('/alive')
def do_alive():
    return "OK"


@get('/status')
def do_status():
    return {"default_volume": default_volume, "announces_enabled": announces_enabled}


@get('/set_default_volume')
def do_set_default_volume():
    global default_volume
    if request.query.default_volume == "":
        return("ERROR: must provide a default_volume integer value!")
    try:
        default_volume = int(request.query.default_volume)
    except:
        return("erreur trying to convert default_volume value to int!?!")
    update_ini()
    if announces_enabled:
        radio_speech("Okay! Je règle mon volume à {}%...".format(default_volume), str(default_volume)+"%")
    return("OK, default_volume has been set to {}%.".format(default_volume))


@get('/enable_announces')
def do_enable_announces():
    global announces_enabled
    announces_enabled = True
    radio_speech("Opératrice à son poste!", str(default_volume)+"%")
    update_ini()
    return("OK, announces_enabled has been set to {}.".format(announces_enabled))


@get('/disable_announces')
def do_disable_announces():
    global announces_enabled
    announces_enabled = False
    radio_speech("Silence radio!", str(default_volume)+"%")
    update_ini()
    return("OK, announces_enabled has been set to {}.".format(announces_enabled))


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
def do_announce():
    """
    brings up a vocal announcement using speech synthesis and a radio fx
    if announces_enabled is False, then the announce will only work if a
    lock has been used (by snowboy, for speech reco/synth dialog)
    """
    global key
    service = request.query.service
    announce = request.query.announce
    m_key = request.query.key
    volume = request.query.volume
    if volume == "":
        volume = str(default_volume)+"%"

    log.info("%s (key=%s): %s (%s)" % (service, m_key, announce, volume))

    now = datetime.now()
    if ((now-key_ts).total_seconds() > keys_lifespan):
        key = ""
    if (m_key != key):
        return("ERROR: key is missing, or invalid/expired")
    if not announces_enabled and m_key == "":
        return("WARNING: announces_enabled is set FALSE, and no key is used, thus no announcement!")
    if radio_speech(announce, volume):
        return("OK")
    else:
        return("ERROR getting the TTS file, check logs...")


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
default_volume = th_config.getint('main', 'default_volume')
announces_enabled = th_config.getboolean('main', 'announces_enabled')
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
