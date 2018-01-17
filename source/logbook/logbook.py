#!/usr/bin/env python3
# coding: utf-8

"""
Basecamp logbook service

dependencies: pushover, SMS, influxdb

(python3 compatible)
"""

from gevent import monkey; monkey.patch_all()
from bottle import run, request, get
import datetime
import requests
from threading import Timer

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import basecamp.tools as tools
import basecamp.db as db


# =======================================================
# Helpers

def add_to_influxdb(log_type, machine, service, message):
    influx_json_body[0]['time'] = datetime.datetime.utcnow().isoformat()
    influx_json_body[0]['fields'] = {'details': message}
    influx_json_body[0]['tags'] = {'type': log_type, 'service': service, 'machine': machine}
    if not db.client.write_points(influx_json_body):
        tools.log.error("ERROR trying to write points to influxDB with JSON_body={}".format(influx_json_body))
        try:
            requests.get(pushover_url, params={'text': "ERROR: cannot write points to influxDB"}, timeout=pushover_timeout)
        except:
            tools.log.error("ERROR trying to reach pushover at:"+pushover_url)


def alive_check():
    tools.log.info("*** performing alive check() ***")
    t = Timer(tools.alive_frequency, alive_check)
    t.start()
    try:
        requests.get(tools.alive_url, params={'service': tools.service_name, 'version': tools.service_version},
                     timeout=tools.alive_timeout)
    except Exception as e:
        tools.log.error(e.__str__())
        tools.log.error("*** ERROR reaching alive_url on "+str(tools.alive_url)+" ***")
        # tools.notify("ERROR", "*** ERROR reaching alive_url on "+str(tools.alive_url)+" ***")
    return


# =======================================================
# URL handlers

@get('/alive')
def do_alive():
    return(tools.service_version)


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
    tools.log.info("%s [%s] [%s] : %s" % (log_type, machine, service, message))
    if (log_type != "DEBUG"):
        add_to_influxdb(log_type, machine, service, message)
        try:
            requests.get(pushover_url, params={'text': "%s [%s] [%s] : %s" % (log_type, machine, service, message)}, timeout=pushover_timeout)
        except:
            tools.log.error("ERROR trying to reach pushover at:"+pushover_url)
        if (log_type == "ALARM"):
            try:
                requests.get(sms_url, params={'msisdn': admin_msisdn, 'text': "%s [%s] [%s] : %s" % (log_type, machine, service, message)}, timeout=sms_timeout)
            except:
                tools.log.error("ERROR trying to reach SMS_operator at:"+sms_url)
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
    for line in reversed(open(tools.logfile_name).readlines()):
        res += line
    res += "</pre></html>"
    return res


# =======================================================
# main loop

if __name__ == "__main__":
    # initialize config/logs
    tools.load_config(optional_service_name="logbook")
    # .ini
    # startup_wait = tools.config.getint('startup', 'wait')
    # hostname = tools.config.get('main', 'hostname')
    # port = tools.config.getint('main', 'port')
    pushover_url = tools.config.get('pushover', 'pushover_url')
    pushover_timeout = tools.config.getint('pushover', 'pushover_timeout')
    sms_url = tools.config.get('sms', 'sms_url')
    admin_msisdn = tools.config.get('sms', 'admin_msisdn')
    sms_timeout = tools.config.getint('sms', 'sms_timeout')
    # also: getfloat, getint, getboolean
    tools.init_logs(formatter='%(asctime)s - %(message)s')
    influx_json_body = db.init()
    # no startup sync for logbook
    tools.log.info("WARNING [%s] [%s] : %s - (re)started!" % (tools.machine_name, tools.service_name, tools.service_version))
    # run baby, run!
    alive_check()
    run(host=tools.hostname, port=tools.port, server='gevent')
