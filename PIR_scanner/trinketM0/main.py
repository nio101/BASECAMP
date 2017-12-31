# trinketM0 demo script #1
# nio101 - tenuki.fr

# dotstar LED => utiliser! :)
# red GPIO #13 led => utiliser aussi! :)

import digitalio
import board
import time
import adafruit_dotstar as dotstar
from digitalio import DigitalInOut, Direction, Pull
import microcontroller


sky_blue = [0, 120, 135]
idle_color = [70, 243, 70]
hit_color = [150, 20, 00]

# One pixel connected internally!
dot = dotstar.DotStar(board.APA102_SCK, board.APA102_MOSI, n=1, brightness=0.2)
dot[0] = sky_blue

led = digitalio.DigitalInOut(board.D13)
led.direction = digitalio.Direction.OUTPUT

# Digital input with pullup on D0

PIR1 = DigitalInOut(board.D0)
PIR1.direction = Direction.INPUT
PIR1.pull = Pull.DOWN

# Digital input with pullup on D2
PIR2 = DigitalInOut(board.D2)
PIR2.direction = Direction.INPUT
PIR2.pull = Pull.DOWN

f_PIR1 = PIR1.value
f_PIR2 = PIR2.value

while True:

	time.sleep(0.5)

	if PIR1.value and not f_PIR1:
		dot[0] = hit_color
		print("PIR1")
		f_PIR1 = True
	elif not PIR1.value and f_PIR1:
		f_PIR1 = False

	if PIR2.value and not f_PIR2:
		dot[0] = hit_color
		print("PIR2")
		f_PIR2 = True
	elif not PIR2.value and f_PIR2:
		f_PIR2 = False

	if not PIR1.value and not PIR2.value:
		dot[0] = idle_color

	#led.value = not led.value
