#!/usr/bin/python
# encoding:utf-8

import gammu
import sys

# Create state machine object
sm = gammu.StateMachine()

# Read ~/.gammurc
sm.ReadConfig(Filename='./.gammurc')

# Connect to phone
sm.Init()

# Reads network information from phone
netinfo = sm.GetNetworkInfo()

# Print information
print 'Network name: %s' % netinfo['NetworkName']
print 'Network code: %s' % netinfo['NetworkCode']
print 'LAC: %s' % netinfo['LAC']
print 'CID: %s' % netinfo['CID']
print netinfo

print sm.GetSMSFolders()
print sm.GetSignalQuality()

