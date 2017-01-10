#!/usr/bin/python
# -*- coding: utf-8 -*-


import zmq
import msgpack
import sys


if len(sys.argv) != 3:
    print "args should be: topic message"
    exit(0)
else:
    topic = sys.argv[1]
    messagedata = sys.argv[2]
# Basecamp ZMQ setup
context = zmq.Context()
# Basecamp send channel
socket_send = context.socket(zmq.PUB)
socket_send.connect("tcp://127.0.0.1:5000")
print("ZMQ connect: PUB on tcp://127.0.0.1:5000 (send)")
print 'sending message...'
socket_send.send("%s %s" % (topic, messagedata))
