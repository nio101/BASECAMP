#!/usr/bin/python
# -*- coding: utf-8 -*-

# interphone debug - send dummy message

import umsgpack
import zmq
import time
import datetime


# ZMQ init
context = zmq.Context()
# muta PUB channel
socket_pub = context.socket(zmq.PUB)
socket_pub.connect("tcp://bc-hq.local:5000")
time.sleep(5)
data = umsgpack.packb([u"test", u"Coucou Nicolas, je te souhaite une bonne soirée..."])
socket_pub.send("%s %s" % ("basecamp.interphone.announce", data))
now = datetime.datetime.now()
print now.year, now.month, now.day, now.hour, now.minute, now.second
