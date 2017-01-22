#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
interphone service

(python2 ONLY - due to ZMQ/msgpack unicode handling)
"""


import logging
import logging.handlers
import configparser
import requests
import umsgpack
import zmq
import time
import os


# =======================================================
# init
service_name = "interphone"
# .ini
th_config = configparser.ConfigParser()
th_config.read(service_name+".ini")
logfile = th_config.get('main', 'logfile')
pushover_url = th_config.get('main', 'pushover_url')
tts_url = th_config.get('main', 'tts_url')
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
socket_pub.connect("tcp://bc-hq.local:5000")
log.info("ZMQ connect: PUB on tcp://bc-hq.local:5000")
# muta SUB channel
socket_sub = context.socket(zmq.SUB)
socket_sub.connect("tcp://bc-hq.local:5001")
topicfilter = "basecamp.interphone.announce"
socket_sub.setsockopt(zmq.SUBSCRIBE, topicfilter)
log.debug("ZMQ connect: SUB on tcp://bc-hq.local:5001")
# give ZMQ some time to setup the channels
time.sleep(1)
poller = zmq.Poller()
poller.register(socket_sub, zmq.POLLIN)

# send a restart info on pushover
# r = requests.get(pushover_url, params = {'text': "le service "+service_name+" a redémarré..."})

# =======================================================
# helpers

def download_file(url):
    #local_filename = url.split('/')[-1]
    local_filename = "last_announce.wav"
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024): 
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
    return local_filename

# =======================================================
# main loop

# scan ZMQ for incoming interphone requests
should_continue = True
while should_continue is True:
    try:
        # ! try different sleep value to decrease the CPU load !
        time.sleep(2)
        socks = dict(poller.poll(0))
    except zmq.ZMQError as e:
        if e.errno == errno.EINTR:
            continue
        else:
            raise
    except KeyboardInterrupt:
        should_continue = False
    if socket_sub in socks and socks[socket_sub] == zmq.POLLIN:
        # new message incoming
        raw_msg = socket_sub.recv()
        topic, messagedata = raw_msg.split(' ', 1)
        (service, announce) = umsgpack.unpackb(messagedata, use_list=True)
        log.info('%s/%s: %s' % (topic, service, announce))
        # request TTS wav file
        r = requests.get(tts_url, params = {'text': announce}, stream=True)
        if r.status_code==200:
            wav_url = r.text
            print(wav_url)
            # download wav file
            local_wav = download_file(wav_url)
            # play wav file
            os.system("aplay "+local_wav)
            # remove the file
            os.remove(local_wav)
        else:
            print("ERROR")
        # could perform snowbow hotword reco too ?
