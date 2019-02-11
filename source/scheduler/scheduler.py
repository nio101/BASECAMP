#!/usr/bin/env python3
# coding: utf-8

"""
scheduler service

dependencies: logbook, interphone

TODO:
    * toutes les 5mn, aller grabber une image sur le net pour 
        - sera utilisé sur la page web d'accueil! :)
    + faire en sorte que scheduler puisse lire mon agenda et me rappeler les trucs pour lesquels j'ai mis un TAG spécifique genre "BASECAMP-1d", et du coup, il me rappelle le RV la veille au soir, à mon retour (ou par SMS, ou les deux). Ou bien "BASECAMP-3h" et il me rappelle le RV 3h avant... :)
        + mettre le calendrier des poubelles! :)
    + pour les annonces d'heure, ajouter des variantes marrantes, et aussi un commentaire... "et tout va bien ici..." ou bien "On a quelques soucis, ici, quand tu auras un moment... merci!". Scanner la présence BT par exemple pour varier en ajoutant les Alias (Nico, Natacha)...
    + conditionner les annonces vocales d'heure en mode cocoon exclusivement.
"""

import requests
import time
import schedule
import datetime
from random import randint
# BC_commons import
from threading import Timer
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import basecamp.tools as tools


# =======================================================
# helpers

# =======================================================

def alive_check():
    # tools.log.info("*** performing alive check() ***")
    t = Timer(tools.alive_frequency, alive_check)
    t.start()
    try:
        requests.get(tools.alive_url, params={'service': tools.service_name, 'version': tools.service_version},
                     timeout=tools.alive_timeout)
    except Exception as e:
        tools.log.error(e.__str__())
        tools.log.error("*** ERROR reaching alive_url on "+str(tools.alive_url)+" ***")
        tools.notify("ERROR", "*** ERROR reaching alive_url on "+str(tools.alive_url)+" ***")
    return


def one_of(m_list):
    return m_list[randint(0, len(m_list)-1)]


# =======================================================
# time announce job


def update_holidays_flag():
    # are we on holidays?
    global holidays_flag
    try:
        r = requests.get(status_url, timeout=20)
    except Exception as e:
        tools.log.error(e.__str__())
        tools.log.error("*** ERROR reaching status_url on "+str(status_url)+" ***")
        tools.notify("ERROR", "*** ERROR reaching status_url on "+str(status_url)+" ***")
    if r.json()[status_field] == status_value:
        holidays_flag = True
    else:
        holidays_flag = False


# =======================================================
# time announce job

def job(h, m, normal_day, holiday_day):
    # are we on holidays?
    global holidays_flag
    if holidays_flag:
        day_config = holiday_day
    else:
        day_config = normal_day

    now = datetime.datetime.today()
    now = now.replace(hour=int(h), minute=int(m))
    res = False
    for _slice in day_config:
        beg = now.replace(hour=int(_slice[0:2]), minute=int(_slice[3:5]))
        end = now.replace(hour=int(_slice[6:8]), minute=int(_slice[9:11]))
        if ((now >= beg) and (now < end)):
            res = True
            break
    if res is True:
        print()
        # choose an announcement
        m_announce = one_of(day_config[_slice])
        if (m == "00"):
            m_time = h+"h"
        else:
            m_time = h+"h"+m
        tools.log.debug("announcing time: "+m_announce.format(m_time))
        try:
            requests.get(interphone_url, params={'service': tools.service_name, 'announce': m_announce.format(m_time)}, timeout=interphone_timeout)
        except Exception as e:
            tools.log.error(e.__str__())
            tools.log.error("*** ERROR reaching interphone on "+str(interphone_url)+" ***")
            tools.notify("ERROR", "*** ERROR reaching interphone on "+str(interphone_url)+" ***")
    else:
        print("(not inside any timeframe)")
    return


# =======================================================
# main stuff

if __name__ == "__main__":
    # initialize config/logs
    tools.load_config()
    tools.init_logs()
    # .ini
    startup_wait = tools.config.getint('startup', 'wait')
    # also: getfloat, getint, getboolean
    interphone_url = tools.config.get('interphone', 'interphone_url')
    interphone_timeout = tools.config.getint('interphone', 'interphone_timeout')

    status_url = tools.config.get('holidays_flag', 'status_url')
    status_field = tools.config.get('holidays_flag', 'status_field')
    status_value = tools.config.get('holidays_flag', 'status_value')

    hello_world = eval(tools.config.get('announcements', 'hello_world'))
    # announcements_time_week = eval(tools.config.get('announcements', 'announcements_time_week'))
    # announcements_time_weekend = eval(tools.config.get('announcements', 'announcements_time_weekend'))
    hour_marks = eval(tools.config.get('announcements', 'hour_marks'))

    monday_work = eval(tools.config.get('announcements', 'monday_work'))
    tuesday_work = eval(tools.config.get('announcements', 'tuesday_work'))
    wednesday_work = eval(tools.config.get('announcements', 'wednesday_work'))
    thursday_work = eval(tools.config.get('announcements', 'thursday_work'))
    friday_work = eval(tools.config.get('announcements', 'friday_work'))
    saturday = eval(tools.config.get('announcements', 'saturday'))
    sunday = eval(tools.config.get('announcements', 'sunday'))
    anyday_holiday = eval(tools.config.get('announcements', 'anyday_holiday'))

    print(monday_work)
    print(type(monday_work))
    for key in monday_work:
        print(key, type(monday_work[key]))

    update_holidays_flag()

    # startup sync & notification
    tools.log.info("--= Restarting =--")
    tools.log.info("sleeping {} seconds for startup sync between services...".format(startup_wait))
    time.sleep(startup_wait)
    tools.notify("WARNING", tools.service_version+" - (re)started!")
    requests.get(interphone_url, params={'service': tools.service_name, 'announce': one_of(hello_world)}, timeout=interphone_timeout)
    # run baby, run!
    alive_check()
    # scheduler init
    hours = []

    # udpate the holiday flag everyday @5am
    schedule.every().day.at("05:00").do(update_holidays_flag)

    # debug
    # job("09", "45", monday_work, anyday_holiday)
    # exit(0)

    # during the week, announce between 6h-22h
    for hour in range(6, 22):
        hours.append('{0:01d}'.format(hour))
    for hour in hours:
        for mn in hour_marks:
            #schedule.every().day.at(hour+":"+mn).do(job, hour, mn)
            schedule.every().monday.at(hour+":"+mn).do(job, hour, mn, monday_work, anyday_holiday)
            schedule.every().tuesday.at(hour+":"+mn).do(job, hour, mn, tuesday_work, anyday_holiday)
            schedule.every().wednesday.at(hour+":"+mn).do(job, hour, mn, wednesday_work, anyday_holiday)
            schedule.every().thursday.at(hour+":"+mn).do(job, hour, mn, thursday_work, anyday_holiday)
            schedule.every().friday.at(hour+":"+mn).do(job, hour, mn, friday_work, anyday_holiday)
    # during the weekend, announce between 9h-22h
    hours = []
    for hour in range(9, 22):
        hours.append('{0:01d}'.format(hour))
    for hour in hours:
        for mn in hour_marks:
            #schedule.every().day.at(hour+":"+mn).do(job, hour, mn)
            schedule.every().saturday.at(hour+":"+mn).do(job, hour, mn, saturday, anyday_holiday)
            schedule.every().sunday.at(hour+":"+mn).do(job, hour, mn, sunday, anyday_holiday)

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
        time.sleep(10)
