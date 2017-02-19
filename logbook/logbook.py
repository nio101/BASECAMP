#!/usr/bin/env python
# coding: utf-8

"""
Basecamp logbook service

(python2/python3 compatible)
note:   webserver may not be multi-threaded/non-blocking.
        if needed, use bottle with gunicorn for example.
"""


from bottle import run, request, get
import logging
import logging.handlers
import configparser


# =======================================================
# init
service_name = "logbook"

# .ini
th_config = configparser.ConfigParser()
th_config.read(service_name+".ini")
logfile = th_config.get('main', 'logfile')
hostname = th_config.get('main', 'hostname')
port = th_config.getint('main', 'port')
# also: getfloat, getint, getboolean

# log
log = logging.getLogger(service_name)
log.setLevel(logging.INFO)
# create file handler
fh = logging.handlers.RotatingFileHandler(
              logfile, maxBytes=500000, backupCount=5)
fh.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s: %(message)s')
fh.setFormatter(formatter)
# add the handlers to the logger
log.addHandler(fh)

# add its own restart info
log.warning("[%s] [%s] : redémarrage" % ("bc-watch", service_name))

# =======================================================
# URL handlers


@get('/alive')
def do_alive():
    return "OK"


@get('/add_to_logbook')
def do_add():
    machine = request.query.machine
    service = request.query.service
    message = request.query.message
    log.info("[%s] [%s] : %s" % (machine, service, message))
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

run(host=hostname, port=port)
