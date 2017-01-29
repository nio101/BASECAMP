#!/usr/bin/python
# -*- coding: utf-8 -*-


import zmq
import umsgpack
import signal


print u"héhé!"
# Basecamp ZMQ setup
context = zmq.Context()
# Basecamp receive channel
socket_receive = context.socket(zmq.SUB)
socket_receive.connect("tcp://bc-hq.local:5001")
topicfilter = ""
socket_receive.setsockopt(zmq.SUBSCRIBE, topicfilter)
print("ZMQ connect: SUB on tcp://bc-hq.local:5001, topics filtering: basecamp")
while True:
    string = socket_receive.recv()
    print string
    topic, messagedata = string.split(' ', 1)
    message = umsgpack.unpackb(messagedata, use_list=True)
    print('%s: %s' % (topic, message))
    for item in message:
        print("\t%s" % item)
