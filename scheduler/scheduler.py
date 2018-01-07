#!/usr/bin/python
# -*- coding: utf-8 -*-

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
import sys
# BC_commons import
from inspect import getsourcefile
from threading import Timer
import os.path
current_dir = os.path.dirname(os.path.abspath(getsourcefile(lambda: 0)))
sys.path.insert(0, current_dir[:current_dir.rfind(os.path.sep)])
import BC_commons as bc
# from BC_commons import influxDB
sys.path.pop(0)  # remove parent dir from sys.path


# =======================================================
# helpers

# =======================================================

def alive_check():
    bc.log.info("*** performing alive check() ***")
    t = Timer(bc.alive_frequency, alive_check)
    t.start()
    try:
        requests.get(bc.alive_url, params={'service': bc.service_name, 'version': bc.version},
                     timeout=bc.alive_timeout)
    except Exception as e:
        bc.log.error(e.__str__())
        bc.log.error("*** ERROR reaching alive_url on "+str(bc.alive_url)+" ***")
        bc.notify("ERROR", "*** ERROR reaching alive_url on "+str(bc.alive_url)+" ***")
    return


# =======================================================
# time announce job

def job(h, m):
    # ajouter des conditions:
    if (m == "00"):
        announce = "Nico! Il est déjà "+h+"h!"
    else:
        announce = "Nico! Il est déjà "+h+"h"+m+"!"
    requests.get(interphone_url, params={'service': bc.service_name, 'announce': announce}, timeout=interphone_timeout)


# =======================================================
# main stuff

# local .ini
startup_wait = bc.config.getint('startup', 'wait')
# also: getfloat, getint, getboolean
interphone_url = bc.config.get('interphone', 'interphone_url')
interphone_timeout = bc.config.getint('interphone', 'interphone_timeout')

# startup sync & notification
bc.log.info("--= Restarting =--")
bc.log.info("sleeping {} seconds for startup sync between services...".format(startup_wait))
time.sleep(startup_wait)
bc.notify("WARNING", bc.service_name+" "+bc.version+" (re)started on machine "+bc.machine_name)

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
