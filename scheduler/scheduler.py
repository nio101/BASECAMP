#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
scheduler service

(python2 ONLY - due to ZMQ/msgpack unicode handling)
"""


import logging
import logging.handlers
import configparser
import requests
import umsgpack
import zmq
import time
import schedule
import re
import sys
import socket


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
# send a restart info to logbook
requests.get(logbook_url, params={'machine': machine_name, 'service': service_name, 'message': "redémarrage"})

# ZMQ init
context = zmq.Context()
# muta PUB channel
socket_pub = context.socket(zmq.PUB)
socket_pub.connect("tcp://bc-hq.local:5000")
log.info("ZMQ connect: PUB on tcp://bc-hq.local:5000")

# send a restart info on pushover
# r = requests.get(pushover_url, params = {'text': "le service "+service_name+" a redémarré..."})

# =======================================================
# main loop


def job(h, m):
    # send a test ZMQ request to interphone service
    d_announce = {
        "0000": "il est minuit!",
        "0015": "il est minuit et quart.",
        "0030": "il est minuit et demie.",
        "0045": "il est une heure moins le quart.",
        "0100": "il est une heure du matin",
        "0115": "il est une heure et quart.",
        "0130": "il est une heure et demie.",
        "0145": "il est deux heures moins le quart.",
        "0200": "il est deux heures du matin.",
        "0215": "il est deux heures et quart.",
        "0230": "il est deux heures et demie.",
        "0245": "il est trois heures moins le quart.",
        "0300": "il est trois heures du matin.",
        "0315": "il est trois heures et quart.",
        "0330": "il est trois heures et demie.",
        "0345": "il est quatre heures moins le quart.",
        "0400": "il est quatre heures du matin.",
        "0415": "il est quatre heures et quart.",
        "0430": "il est quatre heures et demie.",
        "0445": "il est cinq heures moins le quart.",
        "0500": "il est cinq heures du matin.",
        "0515": "il est cinq heures et quart.",
        "0530": "il est cinq heures et demie.",
        "0545": "il est six heures moins le quart.",
        "0600": "il est six heures.",
        "0615": "il est six heures et quart.",
        "0630": "il est six heures et demie.",
        "0645": "il est sept heures moins le quart.",
        "0700": "il est sept heures.",
        "0715": "il est sept heures et quart.",
        "0730": "il est sept heures et demie.",
        "0745": "il est huit heures moins le quart.",
        "0800": "il est huit heures.",
        "0815": "il est huit heures et quart.",
        "0830": "il est huit heures et demie.",
        "0845": "il est neuf heures moins le quart.",
        "0900": "il est neuf heures.",
        "0915": "il est neuf heures et quart.",
        "0930": "il est neuf heures et demie.",
        "0945": "il est dix heures moins le quart.",
        "1000": "il est dix heures .",
        "1015": "il est dix heures et quart.",
        "1030": "il est dix heures et demie.",
        "1045": "il est onze heures moins le quart.",
        "1100": "il est onze heures.",
        "1115": "il est onze heures et quart.",
        "1130": "il est onze heures et demie.",
        "1145": "il est midi moins le quart.",
        "1200": "il est midi.",
        "1215": "il est midi et quart.",
        "1230": "il est midi et demie.",
        "1245": "il est une heure moins le quart.",
        "1300": "il est treize heures.",
        "1315": "il est treize heures quinze.",
        "1330": "il est treize heures trente.",
        "1345": "il est treize heures quarante cinq.",
        "1400": "il est quatorze heures.",
        "1415": "il est quatorze heures quinze.",
        "1430": "il est quatorze heures trente.",
        "1445": "il est quatorze heures quarante cinq.",
        "1500": "il est quinze heures.",
        "1515": "il est quinze heures quinze.",
        "1530": "il est quinze heures trente.",
        "1545": "il est quinze heures quarante cinq.",
        "1600": "il est seize heures.",
        "1615": "il est seize heures quinze.",
        "1630": "il est seize heures trente.",
        "1645": "il est seize heures quarante cinq.",
        "1700": "il est dix-sept heures.",
        "1715": "il est dix-sept heures quinze.",
        "1730": "il est dix-sept heures trente.",
        "1745": "il est dix-sept heures quarante cinq.",
        "1800": "il est dix-huit heures.",
        "1815": "il est dix-huit heures quinze.",
        "1830": "il est dix-huit heures trente.",
        "1845": "il est dix-huit heures quarante cinq.",
        "1900": "il est dix-neuf heures.",
        "1915": "il est dix-neuf heures quinze.",
        "1930": "il est dix-neuf heures trente.",
        "1945": "il est dix-neuf heures quarante cinq.",
        "2000": "il est vingt heures.",
        "2015": "il est vingt heures quinze.",
        "2030": "il est vingt heures trente.",
        "2045": "il est vingt heures quarante cinq.",
        "2100": "il est vingt et une heures.",
        "2115": "il est vingt et une heures quinze.",
        "2130": "il est vingt et une heures trente.",
        "2145": "il est vingt et une heures quarante cinq.",
        "2200": "il est vingt-deux heures.",
        "2215": "il est vingt-deux heures quinze.",
        "2230": "il est vingt-deux heures trente.",
        "2245": "il est vingt-deux heures quarante cinq.",
        "2300": "il est vingt-trois heures.",
        "2315": "il est vingt-trois heures quinze.",
        "2330": "il est vingt-trois heures trente.",
        "2345": "il est vingt-trois heures quarante cinq."
    }
    announce = d_announce[h+m]
    data = umsgpack.packb([u"scheduler", announce])
    socket_pub.send("%s %s" % ("basecamp.interphone.announce", data))
    """
    messagedata = umsgpack.packb(["scheduler", "Coucou! Ca va Nicolas?"])
    print(type(messagedata))
    test = "basecamp.interphone.announce "
    test += messagedata.encode
    socket_pub.send_string(test)
    # socket_pub.send_string("%s %x" % ("basecamp.interphone.announce", messagedata))
    """
hours = []
for hour in range(24):
    hours.append('{0:02d}'.format(hour))
# hour_marks = ["00", "15", "30", "45"]
hour_marks = ["00", "30"]
for hour in hours:
    for mn in hour_marks:
        schedule.every().day.at(hour+":"+mn).do(job, hour, mn)
"""
schedule.every(10).seconds.do(job)
schedule.every().hour.do(job)
schedule.every().day.at("10:30").do(job)
schedule.every().monday.do(job)
schedule.every().wednesday.at("13:15").do(job)
"""
# time.sleep(10)
# schedule.run_all(delay_seconds=2)

while True:
    schedule.run_pending()
    time.sleep(2)
