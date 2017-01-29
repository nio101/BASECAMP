#! /usr/bin/env python
# -*- coding: utf8 -*-

"""
basecampHQ module

Supervises the operations, handles the scripts/behaviors

logs to the console & to '/var/tmp/muta.log'.

nio101 - 01/2013
<insert open source licence here>
"""

import time
import datetime
import sys
import signal
import logging
import logging.handlers
import errno
import ConfigParser
import sqlite3
import zmq
import msgpack

# --------------------------------------------------------------------------

def thermostat_loop(signal, frame):
	global should_rearm_timer
	global log
	should_rearm_timer = True
	return

def is_calendar_on_eco(calendar):
	# get day of week, time of day
	# and check against the calendar
	res = True
	now = datetime.datetime.today()
	time_slices = calendar[now.weekday()]
	for _slice in time_slices:
		beg = now.replace(hour=int(_slice[0:2]),minute=int(_slice[3:5]))
		end = now.replace(hour=int(_slice[6:8]),minute=int(_slice[9:11]))
		if ((now >= beg) and (now < end)):
			res = False
			break
	return res

def record_db(name,value):
	global db
	global cur
	# add name to _codenames if it's a new one	
	cur.execute("select * from _codenames where name=?",[name])
	rows = cur.fetchall()
	if (len(rows)==0):
		# codename not present in table, insert it
		cur.execute("insert into _codenames(name) values (?)",[name])
		cur.execute("select * from _codenames where name=?",[name])
		rows = cur.fetchall()
	elif (len(rows)>1):
		# multiple values with same codenames: fix it!
		log.error("multiple codename in db: name=%s" % name)
		exit(1)
	# get codename's id
	row = rows[0]
	codename_id = row["id"]
	# insert new value into _values
	now = datetime.datetime.now()
	posix_now = now.strftime("%s")
	cur.execute("insert into _values(codename_id,timestamp,value) values (?,?,?)",
		(codename_id,posix_now,value))
	db.commit()
	log.info("ajout en base de '%s': %s" % (name,value))

def read_profile(name):
	global temp_eco
	global temp_conf
	global delta_temp_plus
	global delta_temp_minus
	global calendrier
	# read thermostat parameters from text file
	th_config = ConfigParser.ConfigParser()
	th_config.read(name + ".ini")
	temp_eco = float(th_config.get("thermostat","temp_eco"))
	temp_conf = float(th_config.get("thermostat","temp_conf"))
	delta_temp_plus = float(th_config.get("thermostat","delta_temp_plus"))
	delta_temp_minus = float(th_config.get("thermostat","delta_temp_minus"))
	calendrier = eval(th_config.get("thermostat","calendrier"))

# --------------------------------------------------------------------------

class ThMode:
    ECO, COMFORT, FORCED_OFF, FORCED_ON = range(4)
    
# --------------------------------------------------------------------------    

if __name__=="__main__":

	# create logger
	log = logging.getLogger('basecamp_HQ')
	log.setLevel(logging.DEBUG)
	# create file handler
	# fh = logging.FileHandler('/var/tmp/muta.log')
	fh = logging.handlers.RotatingFileHandler(
              '/var/tmp/basecamp.log', maxBytes=8000000, backupCount=5) 
	fh.setLevel(logging.DEBUG)
	# create console handler
	ch = logging.StreamHandler()
	ch.setLevel(logging.INFO)
	# create formatter and add it to the handlers
	formatter = logging.Formatter('%(asctime)s - [%(name)s] %(levelname)s: %(message)s')
	fh.setFormatter(formatter)
	ch.setFormatter(formatter)
	# add the handlers to the logger
	log.addHandler(fh)
	log.addHandler(ch)

	log.warning("basecamp_HQ is (re)starting !")

	# db init
	local_db = "history.db"
	db = sqlite3.connect(local_db)
	db.row_factory = sqlite3.Row
	cur = db.cursor()
	# create tables if the db has been moved/deleted
	cur.execute("create table if not exists _codenames (\
id integer not null primary key,\
name text not null);")
	cur.execute("create table if not exists _values (\
id integer not null primary key,\
codename_id integer not null references T_codenames,\
timestamp numeric not null,\
value numeric not null\
);")
	db.commit()

	# default values for thermostat
	relay_out = None
	temp_in = None
	temp_eco = 18
	temp_conf = 20
	calendrier = None
	delta_temp = 0.5
	
	# read thermostat parameters from text file
	th_config = ConfigParser.ConfigParser()
	th_config.read("config.ini")
	profile = th_config.get("main","profile")

	# read the active profile
	read_profile(profile)
	
	if (is_calendar_on_eco(calendrier)):
		th_mode = ThMode.ECO
		log.info("th.: mode ECO")
	else:
		th_mode = ThMode.COMFORT
		log.info("th.: mode COMFORT")		
	
	# ZMQ setup
	context = zmq.Context()
	# muta orders channel
	socket_orders = context.socket(zmq.PUB)
	socket_orders.connect("tcp://127.0.0.1:5000");
	log.debug("ZMQ connect: PUB on tcp://127.0.0.1:5000 (orders)")
	# muta_reports channel
	socket_reports = context.socket(zmq.SUB)
	socket_reports.connect("tcp://127.0.0.1:5001");
	topicfilter = ""
	socket_reports.setsockopt(zmq.SUBSCRIBE, topicfilter)
	log.debug("ZMQ connect: SUB on tcp://127.0.0.1:5001, all topics (reports)")
	
	# give ZMQ some time to setup the channels
	time.sleep(1)
	
	# Initialize poll set
	poller = zmq.Poller()
	poller.register(socket_reports, zmq.POLLIN)

	# main loop
	should_continue = True
	should_rearm_timer = True

	while should_continue:
		try:		
			socks = dict(poller.poll(1000))
		except zmq.ZMQError as e:
			if e.errno == errno.EINTR:
				continue
			else:
				raise
		except KeyboardInterrupt:
			should_continue = False
			
		# There's a report!
		if socket_reports in socks and socks[socket_reports] == zmq.POLLIN:
			message = socket_reports.recv()
			#print message
			(title,args) = msgpack.unpackb(message, use_list=True)			
		
			"""
			if (title == "ozw_initial_values"):
				valuesField = eval(args)
				relay_out = valuesField['relais_chaudiere']
				if (relay_out == "True"):
					relay_out = 1
				else:
					relay_out = 0
				temp_in = valuesField['temp_salon']
				temp_in = float(temp_in.replace(',','.'))
				log.info("valeur initiale du relais_chaudiere: %i" % relay_out)
				log.info("valeur initiale de la temperature_lue: %.2f°C" % temp_in)
			"""
				
			if (title == "ozw_value_update"):
				log.debug("%s (%s)" % (title,args))
				valuesField = eval(args)
				# TODO: faire suivre à history
				# faire une fonction qui fait suivre à history pour record db
				# logger variation temp_salon + relais_chaudière => sur update
				# + th_mode + aimed_temp => sur changement de mode
				if ('relais_chaudiere' in valuesField.keys()):
					relay_out = valuesField['relais_chaudiere']
					if (relay_out == "True"):
						relay_out = 1
					else:
						relay_out = 0
					log.info("MAJ du relais_chaudiere: %i" % relay_out)
					# record the new value in the db
					record_db("relais_chaudiere",relay_out)
				elif ('temp_salon' in valuesField.keys()):
					temp_in = valuesField['temp_salon']
					temp_in = float(temp_in.replace(',','.'))
					log.info("MAJ de la temperature_lue: %.2f°C" % temp_in)
					# record the new value in the db
					record_db("temp_salon",temp_in)
					
					# thermostat loop ---								
					if (relay_out == None):
						log.warning("thermostat_loop: relay_out is undefined, forcing it now to OFF!")
						log.debug("sending (ORDERS): ozw_operator_heater_command, {'relais_chaudiere':'False'}")
						msg = msgpack.packb(["ozw_operator_heater_command","{'relais_chaudiere':'False'}"])
						socket_orders.send(msg)
						
					elif (th_mode == ThMode.ECO or th_mode == ThMode.COMFORT):					
						# check calendar & mode update
						if (is_calendar_on_eco(calendrier)):
							if (th_mode == ThMode.COMFORT):
								log.info("therm: switching to eco mode")							
								th_mode = ThMode.ECO
								log.debug("sending (ORDERS): basecamp_HQ_heater_info, {'mode':'ECO'}")
								msg = msgpack.packb(["basecamp_HQ_heater_info","{'mode':'ECO'}"])
								socket_orders.send(msg)	
						else:
							if (th_mode == ThMode.ECO):
								log.info("therm: switching to comfort mode")							
								th_mode = ThMode.COMFORT
								log.debug("sending (ORDERS): basecamp_HQ_heater_info, {'mode':'COMFORT'}")
								msg = msgpack.packb(["basecamp_HQ_heater_info","{'mode':'COMFORT'}"])
								socket_orders.send(msg)	
						if (th_mode == ThMode.ECO):
							log.debug("mode ECO");
						elif (th_mode == ThMode.COMFORT):
							log.debug("mode COMFORT");
						# aimed and delta
						if (th_mode == ThMode.ECO):
							aimed_temp = float(temp_eco)
						else:
							aimed_temp = float(temp_conf)

						log.info("aimed_temp=%.2f, relay=%i" % (aimed_temp,relay_out))

						# hystheresis						
						if (float(temp_in) >= (aimed_temp+float(delta_temp_plus))
							and (relay_out == 1)):
							# stop the heater
							log.info("therm: %.2f reached (%.2f max, %.2f aimed), stopping the heater" % (float(temp_in),(aimed_temp+float(delta_temp_plus)),float(aimed_temp)))
							log.debug("sending (ORDERS): ozw_operator_heater_command, {'relais_chaudiere':'False'}")
							msg = msgpack.packb(["ozw_operator_heater_command","{'relais_chaudiere':'False'}"])
							socket_orders.send(msg)												
						elif ((float(temp_in) <= (aimed_temp-float(delta_temp_minus)))
							and (relay_out == 0)):
							# start the heater
							log.info("therm: %.2f reached (%.2f min, %.2f aimed), starting the heater" % (float(temp_in),(float(aimed_temp)-float(delta_temp_minus)),float(aimed_temp)))
							log.debug("sending (ORDERS): ozw_operator_heater_command, {'relais_chaudiere':'True'}")
							msg = msgpack.packb(["ozw_operator_heater_command","{'relais_chaudiere':'True'}"])
							socket_orders.send(msg)						
						
					elif (th_mode == ThMode.FORCED_OFF):
						if (relay_out == 1):
							log.info("Thermostat mode FORCED_OFF, turning off the heater.")
							log.debug("sending (ORDERS): ozw_operator_heater_command, {'relais_chaudiere':'False'}")
							msg = msgpack.packb(["ozw_operator_heater_command","{'relais_chaudiere':'False'}"])
							socket_orders.send(msg)
					
					elif (th_mode == ThMode.FORCED_ON):
						if (relay_out == 0):
							log.info("Thermostat mode FORCED_ON, turning on the heater.")
							log.debug("sending (ORDERS): ozw_operator_heater_command, {'relais_chaudiere':'True'}")
							msg = msgpack.packb(["ozw_operator_heater_command","{'relais_chaudiere':'True'}"])
							socket_orders.send(msg)					
					# thermostat loop ---
				"""
				else:
					log.error("valeur inconnue!")
				"""
			elif (title == "basecamp_HQ_heater_info_request"):
				# somebody's asking for details about profiles
				# and mode, let's end them
				tmp = '?'
				if (th_mode == ThMode.ECO):
					tmp = 'ECO'
				elif (th_mode == ThMode.COMFORT):
					tmp = 'COMFORT'
				log.debug("sending (ORDERS): basecamp_HQ_heater_info, {'profile':'"+profile+"', 'mode':'"+tmp+"'}")
				msg = msgpack.packb(["basecamp_HQ_heater_info","{'profile':'"+profile+"', 'mode':'"+tmp+"'}"])
				socket_orders.send(msg)	
			elif (title == "basecamp_HQ_heater_profile_change_request"):
				valuesField = eval(args)
				if ('profile' in valuesField.keys()):
					new_profile = valuesField['profile']
					# print "profile change request:", new_profile
					read_profile(new_profile)
					profile = new_profile
					log.debug("sending (ORDERS): basecamp_HQ_heater_info, {'profile':'"+profile+"'}")
					msg = msgpack.packb(["basecamp_HQ_heater_info","{'profile':'"+profile+"'}"])
					socket_orders.send(msg)						
					# write thermostat parameters to config file
					th_config = ConfigParser.ConfigParser()
					th_config.read("config.ini")
					th_config.set('main', 'profile', profile)
					with open('config.ini', 'w') as configfile:
						th_config.write(configfile)

	log.warning("basecamp_HQ halted!")
