#!/usr/bin/python -u

import RPi.GPIO as GPIO
import time

# Configuration
FAN_GPIO_PIN = 20       # BCM pin used to drive PWM fan
PWM_FREQ = 25000        # [Hz] 25kHz for PWM control

PWM_OFF = 0             # the PWM_duty_cycle 0%
PWM_MAX = 100           # the PWM_duty_cycle 100%

FAN_OFF=PWM_OFF         # If no relay connection, this sets the fan speed to the lowest setting (230 RPM - https://www.arctic.ac/en/F12-PWM/AFACO-120P2-GBA01). If relay connection, use the relay to cut the power to the fan to turn it off.

############ define functions ##################
# Set fan speed
def setFanSpeed(PWM_duty_cycle):
  fan.start(PWM_duty_cycle)    # set the speed according to the PWM duty cycle
  return()

################################################
try:
  GPIO.setwarnings(False)
  GPIO.setmode(GPIO.BCM)
  # PWM used to control the fan's speed
  GPIO.setup(FAN_GPIO_PIN, GPIO.OUT, initial=GPIO.LOW)
  fan = GPIO.PWM(FAN_GPIO_PIN,PWM_FREQ)
  setFanSpeed(PWM_OFF)

  counter= 0

  while (counter < 5):
    duty_cycle = PWM_MAX*counter/4
    setFanSpeed(duty_cycle)
    time.sleep(4)
    print("Duty cycle:: {:.2f}".format(duty_cycle))
    counter += 1

# trap a CTRL+C keyboard interrupt
except KeyboardInterrupt:
  setFanSpeed(FAN_OFF)
  GPIO.cleanup() # resets all GPIO ports used by this function
