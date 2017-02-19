#!/usr/bin/env python3
# coding: utf-8

"""
power monitoring service

use french power supply 'teleinfo' service to get the power consuption metrics
and push them to influxdb

for python3 (for python2, don't use the readline() str/ascii conversion)
<insert open source licence here>
"""


import logging
import logging.handlers
import configparser
import requests
from threading import Timer
import time
import datetime
from influxdb import InfluxDBClient
import serial
import re
import sys
import socket


# =======================================================


def export_metrics():
    """
    export the average values of metrics to influxdb
    and resets the values
    """
    global current
    global nb_current
    global power
    global nb_power
    global last_index
    print("... time to export metrics to influxdb!")
    if (last_index is not None) and (nb_power > 0) and (nb_current > 0):
        print("nb_current: %i, nb_power = %i, last_index = %i" % (nb_current, nb_power, last_index))
        current_avg = float("{0:.1f}".format(float(current) / float(nb_current)))
        power_avg = float("{0:.1f}".format(float(power) / float(nb_power)))
        current = 0
        nb_current = 0
        power = 0
        nb_power = 0
        influx_json_body[0]['time'] = datetime.datetime.utcnow().isoformat()
        influx_json_body[0]['fields'] = {'current': current_avg, 'power': power_avg, 'index': last_index}
        print("writing to influxdb: "+str(influx_json_body))
        log.info("writing to influxdb: "+str(influx_json_body))
        try:
            client.write_points(influx_json_body)
        except Exception as e:
            print(e.__str__())
            log.error(e)
            log.error("Error reaching infludb on "+str(influxdb_host)+":"+str(influxdb_port))
            requests.get(logbook_url, params={'text': service_name+" - ERREUR: impossible d'accéder à influxdb!"})
    else:
        print("nothing to export!")
    t = Timer(2*60.0, export_metrics)
    t.start()    


# =======================================================
# init
service_name = re.search("([^\/]*)\.py", sys.argv[0]).group(1)
machine_name = socket.gethostname()

# .ini
th_config = configparser.ConfigParser()
th_config.read(service_name+".ini")
logfile = th_config.get('main', 'logfile')
logbook_url = th_config.get('main', 'logbook_url')
influxdb_host = th_config.get("influxdb", "influxdb_host")
influxdb_port = th_config.get("influxdb", "influxdb_port")
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
# send a restart info to logbook
requests.get(logbook_url, params={'machine': machine_name, 'service': service_name, 'message': "redémarrage"})

# influxdb init
client = InfluxDBClient(influxdb_host, influxdb_port)
client.switch_database('basecamp')
log.info("influxdb will be contacted on "+str(influxdb_host)+":"+str(influxdb_port))
influx_json_body = [
    {
        "measurement": "power",
        "tags": {},
        "time": "",
        "fields": {}
    }
]

# var init
current = 0
nb_current = 0
power = 0
nb_power = 0
last_index = None

# =======================================================
# main loop

# TODO: use scheduler to send regularly the aimed_temp+relay_out values to influxdb

t = Timer(2*60.0, export_metrics)
t.start()

p_current = re.compile("IINST ([0-9]*) .*")
p_power = re.compile("PAPP ([0-9]*) .*")
p_index = re.compile("BASE ([0-9]*) .*")

print("reading from '/dev/ttyAMA0'...")
with serial.Serial(port='/dev/ttyAMA0', baudrate=1200, bytesize=serial.SEVENBITS, parity=serial.PARITY_EVEN, rtscts=True, stopbits=serial.STOPBITS_ONE) as ser:
    while True:
        new_line = str(ser.readline(), 'ascii')
        # print(new_line)
        res = p_current.search(new_line)
        #print(res)
        if (res is not None):
            current = current + int(res.group(1))
            nb_current = nb_current + 1
            print('C', end='')
        else:
            res = p_power.search(new_line)
            if (res is not None):
                power = power + int(res.group(1))
                nb_power = nb_power + 1
                print('P', end='')
            else:
                res = p_index.search(new_line)
                if (res is not None):
                    last_index = int(res.group(1))
                    print('I', end='')
                    sys.stdout.flush()

