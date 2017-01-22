#!/usr/bin/python
# -*- coding: utf-8 -*-


"""
lightpack test

blabla

Copyright (2015-2016) Nicolas Barthe,
distributed as open source under the terms
of the GNU General Public License (see COPYING.txt)
"""


import lightpack
from time import sleep
import sys

# Configuration
host = 'localhost' # (default)
port = 3636 # (default)
led_map = [ # Optional aliases for the LEDs in order
    'bottom-right',
    'right-bottom',
    'right-top',
    'top-far-right',
    'top-right',
    'top-left',
    'top-far-left',
    'left-top',
    'left-bottom',
    'bottom-left',
]
# api_key = '{secret-code}' # Default is None
api_key = '{3b4d4219-5753-460f-a852-54221b44a0d2}'

# Connect to the Lightpack API
lp = lightpack.Lightpack(led_map=led_map)
try:
    lp.connect()
except lightpack.CannotConnectError as e:
    print repr(e)
    sys.exit(1)

print "connected"

# Lock the Lightpack so we can make changes
lp.lock()

lp.turnOn()
sleep(0.1)
lp.setSmoothness(100)
sleep(0.1)
lp.setBrightness(10)
sleep(0.1)

"""
# Flash green three times
for i in range(3):
    # The American spellings such as setColorToAll are available as aliases
    lp.setColourToAll((0, 0, 0))
    sleep(2)
    print i
    lp.setColourToAll((255, 255, 255))
    sleep(2)

for i in range(3):
    lp.setBrightness(10)
    sleep(2)
    print i
    lp.setBrightness(100)
    sleep(2)
"""

for i in range(6):
    for led in led_map:
        lp.setColour(led, (255, 255, 255))
        sleep(0.25)
        lp.setColour(led, (0, 0, 0))

lp.turnOff()

# Unlock to release control (the disconnect method actually calls this 
# automatically, but it is often useful on its own so is here for informational 
# purposes)
lp.unlock()

# Disconnect
lp.disconnect()
