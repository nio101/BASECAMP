#!/usr/bin/env python3
# coding: utf-8

"""
Basecamp logbook service

dependencies: pushover, SMS, influxdb

(python3 compatible)
note:   webserver may not be multi-threaded/non-blocking.
        if needed, use bottle with gunicorn for example.
"""

from bottle import run, request, get
import logging
import logging.handlers
import configparser
import socket
from influxdb import InfluxDBClient
import datetime
import requests


# =======================================================
# init
# service_name = re.search("([^\/]*)\.py", sys.argv[0]).group(1)
service_name = "logbook"
machine_name = socket.gethostname()

# .ini
th_config = configparser.ConfigParser()
th_config.read(service_name+".ini")
logfile = th_config.get('main', 'logfile')
hostname = th_config.get('main', 'hostname')
port = th_config.getint('main', 'port')
pushover_url = th_config.get('main', 'pushover_url')
sms_url = th_config.get('main', 'sms_url')
admin_msisdn = th_config.get('main', 'admin_msisdn')
pushover_timeout = th_config.getint('main', 'pushover_timeout')
sms_timeout = th_config.getint('main', 'sms_timeout')
influxdb_host = th_config.get("influxdb", "influxdb_host")
influxdb_port = th_config.get("influxdb", "influxdb_port")
# also: getfloat, getint, getboolean

# log
log = logging.getLogger(service_name)
log.setLevel(logging.DEBUG)
# create file handler
fh = logging.handlers.TimedRotatingFileHandler(logfile, when='midnight', backupCount=7)
fh.setLevel(logging.DEBUG)
# create console hangler with higher level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# create formatter and add it to the handlers
# formatter = logging.Formatter('%(asctime)s - [%(name)s] %(levelname)s: %(message)s')
formatter = logging.Formatter('%(asctime)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
log.addHandler(fh)
log.addHandler(ch)

# influxdb init
client = InfluxDBClient(influxdb_host, influxdb_port)
client.switch_database('basecamp')
log.info("influxdb will be contacted on "+str(influxdb_host)+":"+str(influxdb_port))
influx_json_body = [
    {
        "measurement": "logs",
        "tags": {},
        "time": "",
        "fields": {}
    }
]

# add its own restart info
log.info("WARNING [%s] [%s] : redémarrage" % (machine_name, service_name))


# =======================================================
# Helpers

def add_to_influxdb(log_type, machine, service, message):
    influx_json_body[0]['time'] = datetime.datetime.utcnow().isoformat()
    influx_json_body[0]['fields'] = {'details': message}
    influx_json_body[0]['tags'] = {'type': log_type, 'service': service, 'machine': machine}
    # log.info("writing to influxdb: "+str(influx_json_body))
    try:
        client.write_points(influx_json_body)
    except Exception as e:
        print(e.__str__())
        log.error(e)
        log.error("ERROR reaching infludb on "+str(influxdb_host)+":"+str(influxdb_port))
        # requests.get(sms_url, params={'msisdn': admin_msisdn, 'text': "ERREUR! impossible d'accéder à influxdb!"}, timeout=sms_timeout)
        try:
            requests.get(pushover_url, params={'text': "ERREUR! impossible d'accéder à influxdb!"}, timeout=pushover_timeout)
        except:
            log.error("ERROR trying to reach pushover at:"+pushover_url)


# =======================================================
# URL handlers

@get('/alive')
def do_alive():
    return "OK"


@get('/add_to_logbook')
def do_add():
    log_type = request.query.log_type
    if log_type not in ["DEBUG", "WARNING", "INFO", "ERROR", "ALARM"]:
        return "ERROR: log_type not in [DEBUG,WARNING,INFO,ERROR,ALARM]!"
    machine = request.query.machine
    if machine == "":
        return "ERROR: machine field should NOT be None"
    service = request.query.service
    if service == "":
        return "ERROR: service field should NOT be None"
    message = request.query.message
    if message == "":
        return "ERROR: message field should NOT be None"
    log.info("%s [%s] [%s] : %s" % (log_type, machine, service, message))
    if (log_type != "DEBUG"):
        add_to_influxdb(log_type, machine, service, message)        
        try:
            requests.get(pushover_url, params={'text': "%s [%s] [%s] : %s" % (log_type, machine, service, message)}, timeout=pushover_timeout)
        except:
            log.error("ERROR trying to reach pushover at:"+pushover_url)
        if (log_type == "ALARM"):
            try:
                requests.get(sms_url, params={'msisdn': admin_msisdn, 'text': "%s [%s] [%s] : %s" % (log_type, machine, service, message)}, timeout=sms_timeout)
            except:
                log.error("ERROR trying to reach SMS_operator at:"+sms_url)
    return "OK"


@get('/get_logbook')
def do_get():
    res = "<meta charset=\"UTF-8\">"
    res += "<meta http-equiv=\"refresh\" content=\"5\">\
    <meta http-equiv=\"cache-control\" content=\"max-age=0\" />\
    <meta http-equiv=\"cache-control\" content=\"no-cache\" />\
    <meta http-equiv=\"expires\" content=\"0\" />\
    <meta http-equiv=\"expires\" content=\"Tue, 01 Jan 1980 1:00:00 GMT\" />\
    <meta http-equiv=\"pragma\" content=\"no-cache\" />"
    res += "<html><h2>Basecamp Logbook:</h2><pre>"
    for line in reversed(open(logfile).readlines()):
        res += line
    res += "</pre></html>"
    return res


# =======================================================
# main loop

run(host=hostname, port=port, server='gunicorn', workers=2)
