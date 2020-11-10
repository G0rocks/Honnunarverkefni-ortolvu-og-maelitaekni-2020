import digitalio
from board import *
import time

# Solid State Relay (SSR)
SSR = digitalio.DigitalInOut(D23)
SSR.direction = digitalio.Direction.OUTPUT

teljari = 0

while (teljari<4):
  SSR.value = True
  time.sleep(2)
  SSR.value = False
  time.sleep(2)
  teljari = teljari + 1
  print ("Buid ad slokkva/kveikja: {} sinnum".format(teljari))