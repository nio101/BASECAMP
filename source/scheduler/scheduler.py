#!/usr/bin/env python3
# coding: utf-8

"""
scheduler service

dependencies: logbook, interphone

TODO:
    + donner plus de vocabulaire aux annonces du scheduler / heure
    + toutes les 30mn le matin quand je bosse, mais pas quand je suis en vacances (profil de chauffage sur semaine_vacances), ou bien le week-end!
    + sinon toutes les heures, et le week-end et si vacances, pas avant 10h, et pas après 22h!
    * toutes les 5mn, aller grabber une image du flux vidéo des carpes ! :)
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

def job(h, m):
    # choose an announcement
    if (datetime.datetime.today().weekday() >= 5):  # weekend
        m_announce = one_of(announcements_time_weekend)
    else:
        m_announce = one_of(announcements_time_week)
    if (m == "00"):
        m_time = h+"h"
    else:
        m_time = h+"h"+m
    requests.get(interphone_url, params={'service': tools.service_name, 'announce': m_announce.format(m_time)}, timeout=interphone_timeout)


# =======================================================
# main stuff

if __name__ == "__main__":
    # initialize config/logs
    tools.load_config()
    tools.init_logs()
    # .ini
    startup_wait = tools.config.getint('startup', 'wait')
    startup_wait = tools.config.getint('startup', 'wait')
    # also: getfloat, getint, getboolean
    interphone_url = tools.config.get('interphone', 'interphone_url')
    interphone_timeout = tools.config.getint('interphone', 'interphone_timeout')
    hello_world = eval(tools.config.get('announcements', 'hello_world'))
    announcements_time_week = eval(tools.config.get('announcements', 'announcements_time_week'))
    announcements_time_weekend = eval(tools.config.get('announcements', 'announcements_time_weekend'))

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
    # announce only between 7h00-22h30
    for hour in range(7, 23):
        hours.append('{0:01d}'.format(hour))
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
        time.sleep(10)
