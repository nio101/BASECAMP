#!/usr/bin/env python3
# coding: utf-8

"""
heater service

- depends on: logbook, influxdb
- for python3
- published under GNU GENERAL PUBLIC LICENSE (see LICENCE file)
"""

import logging
import logging.handlers
import configparser
import requests
from threading import Timer
# import umsgpack
# import zmq
import time
import datetime
from bottle import run, request, get
import glob
import os
from influxdb import InfluxDBClient
import re
import sys
import socket
import maya


# sudo apt-get -y install python3-rpi.gpio
try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error importing RPi.GPIO!  This is probably because you need superuser privileges.  You can achieve this by using 'sudo' to run your script")
    exit(1)

# =======================================================


def send_to_logbook(log_type, msg):
    try:
        requests.get(logbook_url, params={'log_type': log_type, 'machine': machine_name, 'service': service_name, 'message': msg},
                     timeout=logbook_timeout)
    except Exception as e:
        log.error(e.__str__())
        log.error("*** ERROR reaching logbook on "+str(logbook_url)+" ***")


class ThMode:   # ThMode reflects the current heating mode
    ECO, COMFORT = range(2)


def check_applicable_profile():
    """
    determine which profile should be used, and read it
    remove any expired profile from suppl_profile and except_profile
    """
    global current_profile
    global base_profile
    global except_profile
    global except_expiration
    global suppl_profile
    global suppl_expiration

    try:
        if except_profile != "":
            # is it expired?
            now = maya.now()
            if now > except_expiration:
                notify("removing except_profile \'{}\' that expired {}.".format(except_profile, except_expiration.slang_time()))
                except_profile = ""
                except_expiration = None
                update_ini()
            else:
                # not expired, then applicable
                if current_profile != except_profile:
                    current_profile = except_profile
                    notify("except_profile \'{}\' applicable for {}.".format(except_profile, except_expiration.slang_time()))
                    read_profile_settings(current_profile)

        if (except_profile == "") and (suppl_profile != ""):
            # is it expired?
            now = maya.now()
            if now > suppl_expiration:
                notify("removing suppl_profile \'{}\' that expired {}.".format(suppl_profile, suppl_expiration.slang_time()))
                suppl_profile = ""
                suppl_expiration = None
                update_ini()
            else:
                # not expired, then applicable
                if current_profile != suppl_profile:
                    current_profile = suppl_profile
                    notify("suppl_profile \'{}\' applicable for {}.".format(suppl_profile, suppl_expiration.slang_time()))
                    read_profile_settings(current_profile)

        if (except_profile == "") and (suppl_profile == ""):
            # use the base_profile
            if current_profile != base_profile:
                current_profile = base_profile
                notify("base_profile \'{}\' is becoming the current profile.".format(current_profile))
                read_profile_settings(current_profile)
    except:
        notify("ERROR", "check_applicable_profile() failed!?! check the program's STDOUT!")
    return


def notify(msg):
    """
    proper notification tryout
    """
    log.info(msg)
    send_to_logbook("INFO", msg)


def read_profile_settings(name):
    """
    read the profile characteristics from the corresponding .ini file
    """
    global temp_eco
    global temp_conf
    global delta_temp_plus
    global delta_temp_minus
    global calendar
    global main_sensor_calendar
    global service_name
    global current_profile
    # read thermostat parameters from text file
    log.info("loading profile '"+current_profile+"'")
    sub_th_config = configparser.ConfigParser()
    sub_th_config.read("profiles/"+name+".ini")
    temp_eco = float(sub_th_config.get("thermostat", "temp_eco"))
    temp_conf = float(sub_th_config.get("thermostat", "temp_conf"))
    delta_temp_plus = float(sub_th_config.get("thermostat", "delta_temp_plus"))
    delta_temp_minus = float(sub_th_config.get("thermostat", "delta_temp_minus"))
    calendar = eval(sub_th_config.get("thermostat", "calendar"))
    main_sensor_calendar = eval(sub_th_config.get("thermostat", "main_sensor_calendar"))
    # requests.get(logbook_url, params={'log_type': "INFO", 'machine': machine_name, 'service': service_name, 'message': "profil de chauffage=="+name})


def update_ini():
    """
    when any change to the configuration needs to be saved,
    save it to .ini in case of reboot/restart
    """
    global th_config
    global current_profile
    global base_profile
    global except_profile
    global except_expiration
    global suppl_profile
    global suppl_expiration

    th_config.set("heating", "base_profile", base_profile)

    if suppl_profile != "":
        th_config.set("heating", "suppl_profile", suppl_profile)
        suppl_expiration_txt = suppl_expiration.rfc3339()
        th_config.set("heating", "suppl_expiration", suppl_expiration_txt)
    else:
        th_config.set("heating", "suppl_profile", "")
        th_config.set("heating", "suppl_expiration", "")

    if except_profile != "":
        th_config.set("heating", "except_profile", except_profile)
        except_expiration_txt = except_expiration.rfc3339()
        th_config.set("heating", "except_expiration", except_expiration_txt)
    else:
        th_config.set("heating", "except_profile", "")
        th_config.set("heating", "except_expiration", "")

    with open(service_name+".ini", 'w') as configfile:
        th_config.write(configfile)
    return


def determine_sensors():
    global main_sensor
    global secondary_sensor
    global main_sensor_calendar
    res = False
    now = datetime.datetime.today()
    for _slice in main_sensor_calendar:
        print(_slice)
        beg = now.replace(hour=int(_slice[0:2]), minute=int(_slice[3:5]))
        end = now.replace(hour=int(_slice[6:8]), minute=int(_slice[9:11]))
        if ((now >= beg) and (now < end)):
            res = True
            break
    if res is True:
        return (main_sensor, secondary_sensor)
    else:
        return (secondary_sensor, main_sensor)


def is_calendar_on_eco(calendar):
    """
    get day of week, time of day end check against the calendar
    set for the current profile to determine if heating mode is ECO
    """
    res = True
    now = datetime.datetime.today()
    time_slices = calendar[now.weekday()]
    for _slice in time_slices:
        print(_slice)
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
            log.error(e.__str__())
            log.error("Error reaching infludb on "+str(influxdb_host)+":"+str(influxdb_port))
            send_to_logbook("ERROR", "Can't reach influxdb!")


# =======================================================
# influxdb export timer function - every 5mn
def timer_export_influxdb():
    t2 = Timer(5*60.0, timer_export_influxdb)
    t2.start()
    export_to_influxdb()


# check temp update and determine relay output accordingly
def check_temp_update():
    global th_mode
    global temp_in
    global sec_temp_in
    global relay_out
    global log
    global aimed_temp
    global delta_temp_plus
    global delta_temp_minus

    t = Timer(30, check_temp_update)
    t.start()

    check_applicable_profile()

    (sensor_name, sec_sensor_name) = determine_sensors()
    try:
        payload = {'db': "basecamp", 'q': "SELECT LAST(\"Tmp\") FROM \"muta\" WHERE unit='"+sensor_name+"'"}
        r = requests.get(influxdb_query_url, params=payload)
    except (requests.exceptions.RequestException, requests.exceptions.ConnectionError) as e:
        log.error(e.__str__())
        send_to_logbook("ERROR", "Can't reach influxdb!")
    except:
        log.error("Unexpected error:"+sys.exc_info()[0])
        send_to_logbook("ERROR", "Can't reach influxdb!")
    else:
        res = r.json()["results"][0]["series"][0]["values"][0]
        timestamp = res[0]
        temp_in = float(res[1])
        log.info("input temperature (from sensor '%s') updated to: %.2f°C @ %s" % (sensor_name, temp_in, str(timestamp)))

    try:
        payload = {'db': "basecamp", 'q': "SELECT LAST(\"Tmp\") FROM \"muta\" WHERE unit='"+sec_sensor_name+"'"}
        r = requests.get(influxdb_query_url, params=payload)
    except (requests.exceptions.RequestException, requests.exceptions.ConnectionError) as e:
        log.error(e.__str__())
        send_to_logbook("ERROR", "Can't reach influxdb!")
    except:
        log.error("Unexpected error:"+sys.exc_info()[0])
        send_to_logbook("ERROR", "Can't reach influxdb!")
    else:
        res = r.json()["results"][0]["series"][0]["values"][0]
        timestamp = res[0]
        sec_temp_in = float(res[1])
        log.info("input temperature (from sensor '%s') updated to: %.2f°C @ %s" % (sec_sensor_name, sec_temp_in, str(timestamp)))

        # ------------------------------------------------------------------------------------------
        # heating command update loop
        need_influxdb_update = False
        # check calendar & mode update
        if (is_calendar_on_eco(calendar)):
            if (th_mode == ThMode.COMFORT):
                log.info("switching to ECO mode")
                th_mode = ThMode.ECO
        else:
            if (th_mode == ThMode.ECO):
                log.info("switching to COMFORT mode")
                th_mode = ThMode.COMFORT
        # aimed and delta
        if (th_mode == ThMode.ECO):
            new_aimed_temp = float(temp_eco)
        else:
            new_aimed_temp = float(temp_conf)
        if (new_aimed_temp != aimed_temp):
            aimed_temp = new_aimed_temp
            need_influxdb_update = True

        log.info("aimed_temp=%.2f, relay=%i" % (aimed_temp, relay_out))

        should_stop = float(temp_in) >= (aimed_temp+float(delta_temp_plus)) and (relay_out == 1)
        #should_stop_bis = float(sec_temp_in) >= max_temp and (relay_out == 1)
        should_start = float(temp_in) <= (aimed_temp-float(delta_temp_minus)) and (relay_out == 0)
        #should_start_bis = float(sec_temp_in) < max_temp
        # hystheresis
        if should_stop:
            # stop the heater
            if should_stop:
                log.info("Main sensor temp: %.2f. Goal reached (%.2f max, %.2f aimed), stopping the heater" % (float(temp_in), (aimed_temp+float(delta_temp_plus)), float(aimed_temp)))
            #if should_stop_bis:
            #    log.info("Secondary sensor temp: %.2f. Maximum reached (%.2f max), stopping the heater" % (float(sec_temp_in), sec_temp_in))
            # switch using GPIO + check with probe
            log.info("resetting the heater relay")
            GPIO.output(reset, 1)
            time.sleep(0.02)
            GPIO.output(reset, 0)
            if GPIO.input(probe):
                log.info("relay probe is HIGH")
                # alarm if probe is not LOW
                log.error("unable to reset heater relay, stopping here")
                send_to_logbook("ERROR", "Unable to reset heater relay!")
                exit(1)
            else:
                log.info("heater latching relay is OFF")
            # send alarm if probe not ok
            relay_out = 0
            need_influxdb_update = True
            # log.debug("sending (ORDERS): ozw_operator_heater_command, {'relais_chaudiere':'False'}")
            # msg = msgpack.packb(["ozw_operator_heater_command","{'relais_chaudiere':'False'}"])
            # socket_orders.send(msg)
        # elif should_start and should_start_bis:
        elif should_start:
            # start the heater
            log.info("Main sensor temp: %.2f. Low limit reached (%.2f min, %.2f aimed), starting the heater" % (float(temp_in), (float(aimed_temp)-float(delta_temp_minus)), float(aimed_temp)))
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
                send_to_logbook("ERROR", "Unable to set heater relay!")
                exit(1)
            # send alarm if probe not ok
            relay_out = 1
            need_influxdb_update = True
            # log.debug("sending (ORDERS): ozw_operator_heater_command, {'relais_chaudiere':'True'}")
            # msg = msgpack.packb(["ozw_operator_heater_command","{'relais_chaudiere':'True'}"])
            # socket_orders.send(msg)
        elif should_start and not should_start_bis:
            # can't start because max temp reached on secondary sensor
            log.info("Should start because main sensor temp: %.2f. Low limit is reached (%.2f min, %.2f aimed)." % (float(temp_in), (float(aimed_temp)-float(delta_temp_minus)), float(aimed_temp)))
            log.info("But we can't because the secondary sensor temp: %.2f is too high (%.2f max)." % (float(sec_temp_in), sec_temp_in))
        if need_influxdb_update is True:
            export_to_influxdb()
        # ------------------------------------------------------------------------------------------


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
    global current_profile
    global profile_list
    if th_mode == ThMode.ECO:
        str_mode = "ECO"
    else:
        str_mode = "CONFORT"
    if suppl_expiration is None:
        suppl_exp_txt = ""
    else:
        suppl_exp_txt = suppl_expiration.slang_time()
    if except_expiration is None:
        except_exp_txt = ""
    else:
        except_exp_txt = except_expiration.slang_time()
    status = {'base_profile': base_profile, 'suppl_profile': suppl_profile, 'except_profile': except_profile,
              'current_profile': current_profile, 'calendar': calendar, 'main_sensor_calendar': main_sensor_calendar,
              'profile_list': profile_list, 'temp_in': temp_in, 'sec_temp_in': sec_temp_in, 'relay_out': relay_out,
              'th_mode': str_mode, 'temp_eco': temp_eco, 'temp_conf': temp_conf, 'aimed_temp': aimed_temp,
              'suppl_expiration': suppl_exp_txt, 'except_expiration': except_exp_txt}
    return(status)


@get('/set_base_profile')
def do_set_base_profile():
    global profile_list
    global base_profile
    if request.query.profile in profile_list:
        base_profile = request.query.profile
        update_ini()
        check_applicable_profile()
        return("OK")
    else:
        return("ERROR: profile not found")


@get('/set_suppl_profile')
def do_set_suppl_profile():
    global profile_list
    global suppl_profile
    global suppl_expiration
    global timezone
    if request.query.profile == "":
        return("ERROR: profile parameter missing!")
    elif request.query.profile == "None":
        notify("removing suppl_profile \'{}\' that would have expired {}.".format(suppl_profile, suppl_expiration.slang_time()))
        suppl_profile = ""
        suppl_expiration = None
        update_ini()
        check_applicable_profile()
        return("OK")
    if request.query.profile in profile_list:
        suppl_profile = request.query.profile
        try:
            suppl_expiration = maya.MayaDT.from_rfc2822(request.query.expiration+' '+timezone)
        except:
            return("ERROR: couldn't parse the expiration field. example: '2017-12-23 08:23:45'")
        notify("added suppl_profile \'{}\' that will expire {}.".format(suppl_profile, suppl_expiration.slang_time()))
        update_ini()
        check_applicable_profile()
        return("OK")
    else:
        return("ERROR: profile not found")


@get('/set_except_profile')
def do_set_except_profile():
    global profile_list
    global except_profile
    global except_expiration
    global timezone
    if request.query.profile == "":
        return("ERROR: profile parameter missing!")
    elif request.query.profile == "None":
        notify("removing except_profile \'{}\' that would have expired {}.".format(except_profile, except_expiration.slang_time()))
        except_profile = ""
        except_expiration = None
        update_ini()
        check_applicable_profile()
        return("OK")
    if request.query.profile in profile_list:
        if request.query.expiration == "":
            return("ERROR: expiration parameter missing! example: '2017-12-23 08:23:45'")
        try:
            except_expiration = maya.MayaDT.from_rfc2822(request.query.expiration+' '+timezone)
        except:
            except_expiration = None
            return("ERROR: couldn't parse the expiration field. example: '2017-12-23 08:23:45'")
        except_profile = request.query.profile
        notify("added except_profile \'{}\' that will expire {}.".format(except_profile, except_expiration.slang_time()))
        update_ini()
        check_applicable_profile()
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
logbook_timeout = th_config.getint('main', 'logbook_timeout')
hostname = th_config.get('main', 'hostname')
port = th_config.getint('main', 'port')
wait_at_startup = th_config.getint('main', 'wait_at_startup')
influxdb_host = th_config.get("influxdb", "influxdb_host")
influxdb_port = th_config.get("influxdb", "influxdb_port")
influxdb_query_url = "http://"+influxdb_host+":"+influxdb_port+"/query"
base_profile = th_config.get("heating", "base_profile")
suppl_profile = th_config.get("heating", "suppl_profile")
suppl_expiration_txt = th_config.get("heating", "suppl_expiration")
if (suppl_expiration_txt != ""):
    suppl_expiration = maya.MayaDT.from_rfc3339(suppl_expiration_txt)
else:
    suppl_expiration = None
except_profile = th_config.get("heating", "except_profile")
except_expiration_txt = th_config.get("heating", "except_expiration")
if (except_expiration_txt != ""):
    except_expiration = maya.MayaDT.from_rfc3339(except_expiration_txt)
else:
    except_expiration = None
main_sensor = th_config.get("heating", "main_sensor")
secondary_sensor = th_config.get("heating", "secondary_sensor")
max_temp = th_config.getfloat("heating", "max_temp")
timezone = th_config.get("main", "timezone")

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

time.sleep(wait_at_startup)

log.warning(service_name+" restarted")
# send a restart info to logbook
send_to_logbook("WARNING", "Restarting...")

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

# default values for thermostat - will be overwritten at the next update
relay_out = None
temp_in = None
sec_temp_in = None
temp_eco = 12
temp_conf = 12
delta_temp = 0.5
aimed_temp = None
th_mode = ThMode.ECO
current_profile = ""
calendar = None

# check the profiles list
profile_list = []
os.chdir("profiles/")
for file in glob.glob("*.ini"):
    profile_list.append(file[:-4])
os.chdir("..")

# determine applicable profile & read it
check_applicable_profile()

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
    requests.get(logbook_url, params={'log_type': "ERROR", 'machine': machine_name, 'service': service_name, 'message': "Impossible d'ouvrir le relais!"})
    exit(1)
else:
    log.info("relay probe is LOW")
    log.info("heater latching relay is OFF")
relay_out = 0


# =======================================================
# main loop

t = Timer(1.0, check_temp_update)
t.start()

t2 = Timer(5*60.0, timer_export_influxdb)
t2.start()

run(host=hostname, port=port)
