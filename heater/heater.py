#!/usr/bin/env python
# coding: utf-8

"""
heater service

(python2 compatible)
<insert open source licence here>
"""


import logging
import logging.handlers
import configparser
import requests
from threading import Timer
import umsgpack
import zmq
import time
import datetime
from bottle import run, request, get
import glob
import os
from influxdb import InfluxDBClient
import re
import sys
import socket


try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error importing RPi.GPIO!  This is probably because you need superuser privileges.  You can achieve this by using 'sudo' to run your script")
    exit(1)

# =======================================================


class ThMode:   # ThMode reflects the current heating mode
    ECO, COMFORT = range(2)


def read_profile_settings(name):
    """
    read the profile characteristics from the corresponding .ini file
    """
    global temp_eco
    global temp_conf
    global delta_temp_plus
    global delta_temp_minus
    global calendrier
    global service_name
    # read thermostat parameters from text file
    th_config = configparser.ConfigParser()
    th_config.read("profiles/"+name+".ini")
    temp_eco = float(th_config.get("thermostat", "temp_eco"))
    temp_conf = float(th_config.get("thermostat", "temp_conf"))
    delta_temp_plus = float(th_config.get("thermostat", "delta_temp_plus"))
    delta_temp_minus = float(th_config.get("thermostat", "delta_temp_minus"))
    calendrier = eval(th_config.get("thermostat", "calendrier"))
    log.info("loading profile '"+profile+"'")
    requests.get(logbook_url, params={'machine': machine_name, 'service': service_name, 'message': "profil de chauffage=="+name})


def save_new_profile_to_ini():
    """
    when a new profile is selected, save it to .ini in case of reboot/restart
    """
    global th_config
    global profile
    th_config.set('main', 'profile', profile)
    with open(service_name+".ini", 'w') as configfile:
        th_config.write(configfile)


def is_calendar_on_eco(calendar):
    """
    get day of week, time of day end check against the calendar
    set for the current profile to determine if heating mode is ECO
    """
    res = True
    now = datetime.datetime.today()
    time_slices = calendar[now.weekday()]
    for _slice in time_slices:
        beg = now.replace(hour=int(_slice[0:2]), minute=int(_slice[3:5]))
        end = now.replace(hour=int(_slice[6:8]), minute=int(_slice[9:11]))
        if ((now >= beg) and (now < end)):
            res = False
            break
    return res


def export_to_influxdb():
    global relay_out
    global aimed_temp
    global service_name
    global log
    global client
    global influx_json_body
    if (relay_out is not None) and (aimed_temp is not None):
        influx_json_body[0]['time'] = datetime.datetime.utcnow().isoformat()
        influx_json_body[0]['fields'] = {'aimed_temp': aimed_temp, 'relay_out': relay_out}
        log.info("writing to influxdb: "+str(influx_json_body))
        try:
            client.write_points(influx_json_body)
        except Exception as e:
            print e.__str__()
            log.error(e)
            log.error("Error reaching infludb on "+str(influxdb_host)+":"+str(influxdb_port))
            requests.get(logbook_url, params={'machine': machine_name, 'service': service_name, 'message': "ERREUR! impossible d'accéder à influxdb!"})


# =======================================================
# influxdb export timer function - every 5mn
def timer_export_influxdb():
    export_to_influxdb()
    t2 = Timer(5*60.0, timer_export_influxdb)
    t2.start()


# ZMQ check + temp / relay update timer function
def check_temp_update():
    global socks
    global th_mode
    global temp_in
    global relay_out
    global log
    global aimed_temp
    global temp_eco
    global temp_conf
    global delta_temp_plus
    global delta_temp_minus
    try:
        socks = dict(poller.poll(1000))
    except zmq.ZMQError as e:
        if e.errno != errno.EINTR:
            raise
    except KeyboardInterrupt:
        exit(0)

    # a new ZMQ message is available
    if socket_sub in socks and socks[socket_sub] == zmq.POLLIN:
        m_str = socket_sub.recv()
        (topic, messagedata) = m_str.split(' ', 1)
        message = umsgpack.unpackb(messagedata, use_list=True)
        # print message
        # log.info("received ZMQ message on '%s': %s" % (topic, message))
        if ((topic == "basecamp.muta.update") and (message[0] == "salon")):
            m_dict = message[1]
            temp_in = float(m_dict['Tmp'][:-1])
            # print(temp_in)
            # temp_in = float(temp_in.replace(',','.'))
            log.info("input temperature (muta.salon.Tmp) updated to new value: %.2f°C" % temp_in)

            # ------------------------------------------------------------------------------------------
            # heating command update loop
            need_influxdb_update = False
            # check calendar & mode update
            if (is_calendar_on_eco(calendrier)):
                if (th_mode == ThMode.COMFORT):
                    log.info("switching to ECO mode")
                    th_mode = ThMode.ECO
                    # log.debug("sending (ORDERS): basecamp_HQ_heater_info, {'mode':'ECO'}")
                    # msg = msgpack.packb(["basecamp_HQ_heater_info","{'mode':'ECO'}"])
                    # socket_orders.send(msg)
                    # TODO: update influxdb with basecamp/heater/goal_temp = temp for ECO mode
            else:
                if (th_mode == ThMode.ECO):
                    log.info("switching to COMFORT mode")
                    th_mode = ThMode.COMFORT
                    # log.debug("sending (ORDERS): basecamp_HQ_heater_info, {'mode':'COMFORT'}")
                    # msg = msgpack.packb(["basecamp_HQ_heater_info","{'mode':'COMFORT'}"])
                    # socket_orders.send(msg)
                    # TODO: update influxdb with basecamp/heater/goal_temp = temp for ECO mode
            # aimed and delta
            if (th_mode == ThMode.ECO):
                new_aimed_temp = float(temp_eco)
            else:
                new_aimed_temp = float(temp_conf)
            if (new_aimed_temp != aimed_temp):
                aimed_temp = new_aimed_temp
                need_influxdb_update = True

            log.info("aimed_temp=%.2f, relay=%i" % (aimed_temp, relay_out))

            # hystheresis
            if (float(temp_in) >= (aimed_temp+float(delta_temp_plus)) and (relay_out == 1)):
                # stop the heater
                log.info("therm: %.2f reached (%.2f max, %.2f aimed), stopping the heater" % (float(temp_in), (aimed_temp+float(delta_temp_plus)), float(aimed_temp)))
                # switch using GPIO + check with probe
                log.info("resetting the heater relay")
                GPIO.output(reset, 1)
                time.sleep(0.02)
                GPIO.output(reset, 0)
                if GPIO.input(probe):
                    log.info("relay probe is HIGH")
                    # alarm if probe is not LOW
                    log.error("unable to reset heater relay, stopping here")
                    requests.get(logbook_url, params={'machine': machine_name, 'service': service_name, 'message': "ERREUR! impossible d'ouvrir le relais!"})
                    exit(1)
                else:
                    log.info("heater latching relay is OFF")
                # send alarm if probe not ok
                relay_out = 0
                need_influxdb_update = True
                # log.debug("sending (ORDERS): ozw_operator_heater_command, {'relais_chaudiere':'False'}")
                # msg = msgpack.packb(["ozw_operator_heater_command","{'relais_chaudiere':'False'}"])
                # socket_orders.send(msg)
            elif ((float(temp_in) <= (aimed_temp-float(delta_temp_minus))) and (relay_out == 0)):
                # start the heater
                log.info("therm: %.2f reached (%.2f min, %.2f aimed), starting the heater" % (float(temp_in), (float(aimed_temp)-float(delta_temp_minus)), float(aimed_temp)))
                # switch using GPIO + check with probe
                log.info("setting the heater relay")
                GPIO.output(set, 1)
                time.sleep(0.02)
                GPIO.output(set, 0)
                if GPIO.input(probe):
                    log.info("heater latching relay is ON")
                else:
                    log.info("relay probe is LOW")
                    # alarm if probe is not HIGH
                    log.error("unable to set heater relay, stopping here")
                    requests.get(logbook_url, params={'machine': machine_name, 'service': service_name, 'message': "ERREUR! impossible de fermer le relais!"})
                    exit(1)
                # send alarm if probe not ok
                relay_out = 1
                need_influxdb_update = True
                # log.debug("sending (ORDERS): ozw_operator_heater_command, {'relais_chaudiere':'True'}")
                # msg = msgpack.packb(["ozw_operator_heater_command","{'relais_chaudiere':'True'}"])
                # socket_orders.send(msg)
            if need_influxdb_update is True:
                export_to_influxdb()
            # ------------------------------------------------------------------------------------------

        # else:
        #     print("=>ignored.")
        # for item in message:
        #    print("\t%s" % item)

    t = Timer(1.0, check_temp_update)
    t.start()


@get('/alive')
def do_alive():
    return "OK"


@get('/status')
def do_status():
    global th_mode
    global temp_in
    global relay_out
    global log
    global aimed_temp
    global temp_eco
    global temp_conf
    global profile
    global profile_list
    if th_mode == ThMode.ECO:
        str_mode = "ECO"
    else:
        str_mode = "CONFORT"
    status = {'profile': profile, 'profile_list': profile_list, 'temp_in': temp_in, 'relay_out': relay_out,
              'th_mode': str_mode, 'temp_eco': temp_eco, 'temp_conf': temp_conf, 'aimed_temp': aimed_temp, }
    return(status)


@get('/set_profile')
def do_set_profile():
    global profile
    global profile_list
    global th_mode
    m_profile = request.query.profile
    if m_profile in profile_list:
        profile = m_profile
        read_profile_settings(profile)
        if (is_calendar_on_eco(calendrier)):
            th_mode = ThMode.ECO
            log.info("th.: ECO mode")
        else:
            th_mode = ThMode.COMFORT
            log.info("th.: COMFORT mode")
        save_new_profile_to_ini()
        return("OK")
    else:
        return("ERROR: profile not found")


# =======================================================
# init
service_name = re.search("([^\/]*)\.py", sys.argv[0]).group(1)
machine_name = socket.gethostname()

# .ini
th_config = configparser.ConfigParser()
th_config.read(service_name+".ini")
logfile = th_config.get('main', 'logfile')
logbook_url = th_config.get('main', 'logbook_url')
hostname = th_config.get('main', 'hostname')
port = th_config.getint('main', 'port')
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

log.warning(service_name+" restarted")
# send a restart info to logbook
requests.get(logbook_url, params={'machine': machine_name, 'service': service_name, 'message': "redémarrage"})

# influxdb init
client = InfluxDBClient(influxdb_host, influxdb_port)
client.switch_database('basecamp')
log.info("influxdb will be contacted on "+str(influxdb_host)+":"+str(influxdb_port))
influx_json_body = [
    {
        "measurement": "heater",
        "tags": {},
        "time": "",
        "fields": {}
    }
]

"""
Heating configuration is base on a heating profile
+   Profile are described in .ini files, in the profiles/ subdir
    example (work_week):
    [thermostat]
    temp_eco=18.2
    temp_conf=20.2
    delta_temp_plus=0.10
    delta_temp_minus=0.25
    calendrier=[['07h00-08h00','16h30-22h00'],
        ['07h00-08h00','16h30-22h00'],
        ['07h00-22h00'],
        ['07h00-08h00','16h30-22h00'],
        ['07h00-08h00','16h30-22h00'],
        ['07h00-22h00'],
        ['07h00-22h00']]
    It sets up the goal temperature for confort/eco modes, the hystheresis values,
    and the schedule for confort mode
The currently used profile is set in the heater.ini file.
"""
# default values for thermostat
relay_out = None
temp_in = None
temp_eco = 12
temp_conf = 12
calendrier = None
delta_temp = 0.5
aimed_temp = None
# read the current profile
profile = th_config.get("main", "profile")
read_profile_settings(profile)
if (is_calendar_on_eco(calendrier)):
    th_mode = ThMode.ECO
    log.info("th.: ECO mode")
else:
    th_mode = ThMode.COMFORT
    log.info("th.: COMFORT mode")
# check the profiles list
profile_list = []
os.chdir("profiles/")
for file in glob.glob("*.ini"):
    profile_list.append(file[:-4])
os.chdir("..")

# GPIO init
GPIO.setmode(GPIO.BOARD)

# probe: pin #15, GPIO22
# set/reset: pins #16/18, GPIO 24/23
probe = 15
set = 16
reset = 18
GPIO.setup(probe, GPIO.IN)
GPIO.setup(set, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(reset, GPIO.OUT, initial=GPIO.LOW)
# shut down the heater,
# check with probe
log.info("resetting the heater relay")
GPIO.output(reset, 1)
time.sleep(0.02)
GPIO.output(reset, 0)
if GPIO.input(probe):
    log.info("relay probe is HIGH")
    # alarm if probe is not 0
    log.error("unable to reset heater relay, stopping here")
    requests.get(logbook_url, params={'machine': machine_name, 'service': service_name, 'message': "ERREUR! impossible d'ouvrir le relais!"})
    exit(1)
else:
    log.info("relay probe is LOW")
    log.info("heater latching relay is OFF")
relay_out = 0

# ZMQ init
context = zmq.Context()
# muta PUB channel
socket_pub = context.socket(zmq.PUB)
socket_pub.connect("tcp://192.168.1.50:5000")
log.info("ZMQ connect: PUB on tcp://192.168.1.50:5000")
# muta SUB channel
socket_sub = context.socket(zmq.SUB)
socket_sub.connect("tcp://192.168.1.50:5001")
topicfilter = "basecamp.muta.update"
socket_sub.setsockopt(zmq.SUBSCRIBE, topicfilter)
log.debug("ZMQ connect: SUB on tcp://192.168.1.50:5001")
# give ZMQ some time to setup the channels
time.sleep(1)
poller = zmq.Poller()
poller.register(socket_sub, zmq.POLLIN)

# =======================================================
# main loop

# TODO: use scheduler to send regularly the aimed_temp+relay_out values to influxdb

t = Timer(1.0, check_temp_update)
t.start()
t2 = Timer(5*60.0, timer_export_influxdb)
t2.start()
run(host=hostname, port=port)
