#!/usr/bin/python
# encoding:utf-8


import CHIP_IO.GPIO as GPIO
from time import sleep


probe = "CSID0"
set = "CSID2"
reset = "CSID4"

GPIO.cleanup()

GPIO.setup(probe, GPIO.IN)
if GPIO.input(probe):
    print("relay probe is HIGH")
else:
    print("relay probe is LOW")


GPIO.setup(set, GPIO.OUT)
GPIO.output(set, 0)
GPIO.setup(reset, GPIO.OUT)
GPIO.output(reset, 0)

sleep(5)
GPIO.output(reset, 1)
# while True:
#     pass
sleep(0.02)
GPIO.output(reset, 0)
if GPIO.input(probe):
    print("relay probe is HIGH")
else:
    print("relay probe is LOW")

sleep(5)
GPIO.output(set, 1)
# while True:
#     pass
sleep(0.02)
GPIO.output(set, 0)
if GPIO.input(probe):
    print("relay probe is HIGH")
else:
    print("relay probe is LOW")
