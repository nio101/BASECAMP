#! /usr/bin/env python
# -*- coding: utf8 -*-

"""
ZMQ multiple PUB/SUB port forwarder

logs to '/var/tmp/muta.log'.

code is coming from:
https://learning-0mq-with-pyzmq.readthedocs.org/en/latest/pyzmq/devices/forwarder.html
"""

import sys
import logging
import logging.handlers
import zmq


def main():

	pub_port = sys.argv[1]
	sub_port = sys.argv[2]

    # create logger
	log = logging.getLogger('zmq_forwarder')
	log.setLevel(logging.DEBUG)
	# create file handler
	# fh = logging.FileHandler('/var/tmp/muta.log')
	fh = logging.handlers.RotatingFileHandler(
              'basecamp.log', maxBytes=8000000, backupCount=5) 
	fh.setLevel(logging.DEBUG)

	# create formatter and add it to the handlers
	formatter = logging.Formatter('%(asctime)s - [%(name)s] %(levelname)s: %(message)s')
	fh.setFormatter(formatter)
	# add the handlers to the logger
	log.addHandler(fh)
	
	log.warning("zmq_forwarder is (re)starting !")

	try:
		context = zmq.Context(1)
		# Socket facing PUBs
		frontend = context.socket(zmq.SUB)
		frontend.bind("tcp://*:%s" % pub_port)
		        
		frontend.setsockopt(zmq.SUBSCRIBE, "")
        
		# Socket facing SUBs
		backend = context.socket(zmq.PUB)
		backend.bind("tcp://*:%s" % sub_port)

		log.info("ready: from PUB on %s to SUB on port %s" % (pub_port,sub_port))

		zmq.device(zmq.FORWARDER, frontend, backend)        
	except Exception, e:
		print e
		log.warning("zmq_forwarder halted!")
	finally:
		pass
	frontend.close()
	backend.close()
	context.term()

if __name__ == "__main__":
    main()
