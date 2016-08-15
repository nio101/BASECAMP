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

# Flash green three times
for i in range(3):
    # The American spellings such as setColorToAll are available as aliases
    lp.setColourToAll((0, 255, 0))
    sleep(1)
    lp.setColourToAll((0, 0, 0))
    sleep(1)

# Set top right light to yellow
# The Colour class is optional
lp.setColour('top-right', (0,0,255))

sleep(1)

# Set left bottom and left right lights to two other colours
lp.setColours(('left-bottom', (0,255,0)), ('left-top', (255,0,0)))

sleep(1)

# Unlock to release control (the disconnect method actually calls this 
# automatically, but it is often useful on its own so is here for informational 
# purposes)
lp.unlock()

# Disconnect
lp.disconnect()
