#!/usr/bin/python -u

import RPi.GPIO as GPIO
import time
import datetime

# Configuration
TACH_GPIO_PIN = 21      # BCM pin for reading the tachometer
count_time = 2          # seconds for counting sensor changes

############ define functions ##################
def tach_count(sec,GPIO_PIN):
  duration = datetime.timedelta(seconds=sec)      # measure for one second
  end_time = (datetime.datetime.now()+duration)   # set the time when to stop
  current_pin_status = GPIO.input(GPIO_PIN)
  last_pin_status = 2
  counter = 0
  while ( datetime.datetime.now() < end_time):
    current_pin_status=GPIO.input(GPIO_PIN)
    if (current_pin_status != last_pin_status):
#      print(current_pin_status)
      last_pin_status = current_pin_status
      counter += 1
  return (counter)

################################################
try:
  GPIO.setwarnings(False)
  GPIO.setmode(GPIO.BCM)
  # tachometer - from a hall sensor located in the fan
  GPIO.setup(TACH_GPIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

  counter= 0

  while (counter < 5):
    tach_hall_rpm = float(tach_count(count_time,TACH_GPIO_PIN))/count_time/2/2*60
    print("Hall RPM:: {:.2f}".format(tach_hall_rpm))
    counter += 1

# trap a CTRL+C keyboard interrupt
except KeyboardInterrupt:
  setFanSpeed(FAN_OFF)
  GPIO.cleanup() # resets all GPIO ports used by this function
