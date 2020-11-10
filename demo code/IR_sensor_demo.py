#!/usr/bin/python -u

import RPi.GPIO as GPIO
import time
import datetime

# Configuration
IR_GPIO_PIN = 6         # BCM pin used for data from IR module
count_time = 2          # seconds for counting sensor changes
FAN_OFF=0

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

def setFanSpeed(PWM_duty_cycle):
  """
  Function that takes in the percentage of PWM and sends that signal to the fan
  """
  fan.start(PWM_signal*PWM_FREQ)  # Sends the frequency
  return()

################################################
try:
  GPIO.setwarnings(False)
  GPIO.setmode(GPIO.BCM)
  # IR sensor
  GPIO.setup(IR_GPIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

  counter= 0

  while (counter < 5):
    tach_IR_rpm = float(tach_count(count_time,IR_GPIO_PIN))/count_time/2/9*60
    print("IR RPM:: {:.2f}".format(tach_IR_rpm))
    counter += 1

# trap a CTRL+C keyboard interrupt
except KeyboardInterrupt:
  setFanSpeed(FAN_OFF)
  GPIO.cleanup() # resets all GPIO ports used by this function
