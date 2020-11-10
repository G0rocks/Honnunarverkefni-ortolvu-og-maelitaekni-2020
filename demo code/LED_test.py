import digitalio
from board import *
import time

led_white = digitalio.DigitalInOut(D14)
led_white.direction = digitalio.Direction.OUTPUT
led_yellow = digitalio.DigitalInOut(D17)
led_yellow.direction = digitalio.Direction.OUTPUT
led_green = digitalio.DigitalInOut(D27)
led_green.direction = digitalio.Direction.OUTPUT

teljari = 0

while (teljari < 3):
    led_green.value = True
    time.sleep(0.1)
    led_yellow.value = True
    time.sleep(0.1)
    led_white.value = True
    time.sleep(0.1)
    led_green.value = False
    time.sleep(0.1)
    led_yellow.value = False
    time.sleep(0.1)
    led_white.value = False
    time.sleep(0.1)

    teljari = teljari +1