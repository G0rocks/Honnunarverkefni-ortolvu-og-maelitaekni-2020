import RPi.GPIO as GPIO
import time
from time import sleep
import board
import adafruit_dht
import datetime
import numpy as np
import function_config as fc


#----------- Configuration -----------#
FAN_GPIO_PIN = 20       # BCM pin used to drive PWM fan
PWM_FREQ = 25000        # [Hz] 25kHz for PWM control

PWM_OFF = 0             # the PWM_duty_cycle 0%
PWM_MAX = 100           # the PWM_duty_cycle 100%

RELAY_FAN_GPIO_PIN = 26 # BCM pin used to turn RELAY for FAN ON/OFF
RELAY_HEATER_GPIO_PIN = 16 # BCM pin used to turn RELAY for HEATER ON/OFF

dhtDevice = adafruit_dht.DHT22(board.D5) #Hitanemi
deltaT = 0 # breyta til að fylgjast með breyting á hitastigi

#--------------------------------------------#
try:
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    # PWM notað til að stýra viftuhraða
    GPIO.setup(FAN_GPIO_PIN, GPIO.OUT, initial=GPIO.LOW)
    #fan = GPIO.PWM(FAN_GPIO_PIN,PWM_FREQ)
    fc.setFanSpeed(PWM_OFF)
    # Setting up relay for HEATER
    GPIO.setup(RELAY_HEATER_GPIO_PIN, GPIO.OUT, initial=GPIO.HIGH) # HIGH MEANS RELAY IS OFF
    # Setting up relay for FAN
    GPIO.setup(RELAY_FAN_GPIO_PIN, GPIO.OUT, initial=GPIO.HIGH) # HIGH MEANS RELAY IS OFF
    

    #-- Tóm fylki til að vista gögn --# [tími, hitastig, fan_on, duty_cycle, heater_on, oskgildi, error, sum_error]
    head = "tími; hitastig; fan_on; duty_cycle; heater_on; oskgildi; error; sum_error, control_signal"
    gogn = np.empty((0,9), float)
  
    #-------- Prófun á föstu duty cycle ---------#
    duty_cycle = 0
    maxDeltaT = 0.2
    
    fc.heaterOn()
    heater_on = True
    fan_on = False
    isActive = True

    slope_start = 0
    control_signal = 0.0


    # Liður 1
    equil = False
    equil_count = 0
    counter = 0
    sum_error = 0
    startTime = time.time()

    while (isActive):
      temp = fc.measureTemp()
      timi = fc.elapsedTime(startTime)
      oskgildi = fc.oskgildi(slope_start, time.time(), equil_count)
      print('Tími: {:.1f} s'.format(timi), ' Hitastig: {:.1f}°C'.format(temp), ' Óskgildi: {:.1f}°C'.format(oskgildi))
      deltaT = temp - oskgildi
      sum_error += deltaT

      gogn = np.append(gogn, [[timi, temp, fan_on, duty_cycle, heater_on, oskgildi, deltaT, sum_error, control_signal]], axis=0)
      # Athuga hvort jafnvægi hafi náðst
      equil = fc.equilibrium_control(gogn, maxDeltaT)

      if (equil):
        equil_count += 1
        print('equil_count: ', equil_count)
        equil = False
        if (equil_count == 2):
          slope_start = time.time()
          print('slope_start: ', slope_start)
      # Reikna stýrimerki
      control_signal = fc.control(gogn)
      # Nota stýrimerki
      operator = fc.operate(gogn, control_signal)
      duty_cycle = operator[1]
      fan_on = operator[0]
      counter += 1
      if (((timi + startTime - slope_start) > 90) and (slope_start > 0)):
        isActive = False
      time.sleep(2)

    
    np.savetxt('control_test.csv', gogn, delimiter='; ', fmt='%.2f', header = head)

# trap a CTRL+C keyboard interrupt
except KeyboardInterrupt:
    np.savetxt('control_test.csv', gogn, delimiter='; ', fmt='%.2f', header = head)
    fc.setFanSpeed(PWM_OFF)
    fc.heaterOff()
    fc.fanOff()
    GPIO.cleanup() # resets all GPIO ports used by this function


#----------- Núllstilla viftu og hitara í lok keyrslu -----------#
fc.setFanSpeed(0) #slokkva á viftu
fc.fanOff()
fc.heaterOff()
GPIO.cleanup() # resets all GPIO ports used by this function
