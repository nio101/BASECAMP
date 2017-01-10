#!/usr/bin/python
# -*- coding: utf-8 -*-


import zmq
import msgpack
import signal


# Basecamp ZMQ setup
context = zmq.Context()
# Basecamp receive channel
socket_receive = context.socket(zmq.SUB)
socket_receive.connect("tcp://127.0.0.1:5001")
topicfilter = "basecamp"
socket_receive.setsockopt(zmq.SUBSCRIBE, topicfilter)
print("ZMQ connect: SUB on tcp://127.0.0.1:5001, topics filtering: basecamp (receive)")
while True:
    string = socket_receive.recv()
    topic, messagedata = string.split()
    print topic, messagedata
    if topic == 'basecamp.muta.reports' or topic == 'basecamp.muta.orders':
        """
        (alias, values) = msgpack.unpackb(messagedata, use_list=True)
        print "alias:", alias
        print "values:", values
        """
        print '\t', msgpack.unpackb(messagedata, use_list=True)
