#!/usr/bin/python
# encoding:utf-8

import gammu
import sys
from time import sleep


# Create state machine object
sm = gammu.StateMachine()

# Read ~/.gammurc
sm.ReadConfig(Filename='./.gammurc')

# Connect to phone
sm.Init()

while True:
    print sm.GetSignalQuality()
    sleep(5)


