#!/usr/bin/python -u

#!/usr/bin/python -u
import RPi.GPIO as GPIO
import time

# Configuration
RELAY_FAN_GPIO_PIN = 26 # BCM pin used to turn RELAY for FAN ON/OFF
RELAY_HEATER_FAN_GPIO_PIN = 16 # BCM pin used to turn RELAY for HEATER ON/OFF

############ define functions ##################
#
################################################
try:
  GPIO.setwarnings(False)
  GPIO.setmode(GPIO.BCM)
  # Setting up relay for FAN
  GPIO.setup(RELAY_FAN_GPIO_PIN, GPIO.OUT, initial=GPIO.HIGH) # HIGH MEANS RELAY IS OFF
  # Setting up relay for HEATER
  GPIO.setup(RELAY_HEATER_FAN_GPIO_PIN, GPIO.OUT, initial=GPIO.HIGH) # HIGH MEANS RELAY IS OFF

  counter= 0
  while (counter < 2):
    GPIO.output(RELAY_FAN_GPIO_PIN,GPIO.LOW) # Turn the FAN ON
    print("FAN ON")
    time.sleep(10)
    GPIO.output(RELAY_FAN_GPIO_PIN,GPIO.HIGH) # Turn the FAN OFF
    print("FAN OFF")
    time.sleep(10)
    counter += 1

  # IMPORTANT!!
  # Do this at the end.
  # Otherwise the HEATER can be left on
  GPIO.cleanup()

# trap a CTRL+C keyboard interrupt
except KeyboardInterrupt:
  GPIO.cleanup() # resets all GPIO ports used by this function