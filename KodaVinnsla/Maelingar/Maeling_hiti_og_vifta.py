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
    

    #-- Tóm fylki til að vista gögn --# [tími, hitastig, fan_on, duty_cycle, heater_on]
    head = "tími; hitastig; fan_on; duty_cycle; heater_on"
    arr = np.empty((0,5), float)
  
    #-------- Prófun á föstu duty cycle ---------#
    cycles = np.array([0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
    duty_cycle = 0
    maxDeltaT = 0.1
    
    fc.heaterOn()
    heater_on = True
    equil = False
    temp = 0
    while (temp < 25):
      temp = fc.measureTemp()
      time.sleep(4)


    fc.fanOn()
    fan_on = True
    #counter = -1
    counter = 0
    startTime = time.time() #Stilla upphafstima

    while (counter < 11):
      print('umferð: ', counter)
      if ((counter%2)==0):
        duty_cycle = 10
      else:
        duty_cycle = 90

      fc.setFanSpeed(duty_cycle)
      arr = np.empty((0,5), float)
      loopTime = time.time()
      nuna = loopTime
      counter_2 = 1
      while (not(equil and (counter_2 > 30))):
        temp = fc.measureTemp()
        print('Hitastig: ', temp)
        timi = fc.elapsedTime(startTime)
        arr = np.append(arr, [[timi, temp, fan_on, duty_cycle, heater_on]], axis=0)
        equil = fc.is_in_equilibrium(arr, 1, maxDeltaT)
        counter_2 += 1
        time.sleep(1)
      
      counter += 1
      fileName = 'results_' + str(counter) + '.csv'
      np.savetxt(fileName, arr, delimiter='; ', fmt='%.2f', header = head)
    
    """ while (counter < 11):
      if (counter == 0):
        fc.fanOn()
        fan_on = True

      if (counter >= 0):
        duty_cycle = cycles[counter]
        fc.setFanSpeed(duty_cycle)

      loopTime = time.time()
      nuna = loopTime
      while (not(equil and ((nuna-loopTime) > 30))):
        temp = fc.measureTemp()
        print('Hitastig: ', temp)
        timi = fc.elapsedTime(startTime)
        arr = np.append(arr, [[timi, temp, fan_on, duty_cycle, heater_on]], axis=0)
        equil = fc.is_in_equilibrium(arr, 1, maxDeltaT)
        nuna = time.time()
        time.sleep(1)

      counter += 1 """

    #np.savetxt('nidurstodur.csv', arr, delimiter='; ', fmt='%.2f', header = head)

# trap a CTRL+C keyboard interrupt
except KeyboardInterrupt:
    fc.setFanSpeed(PWM_OFF)
    fc.fanOff()
    fc.heaterOff()
    GPIO.cleanup() # resets all GPIO ports used by this function


#----------- Núllstilla viftu og hitara í lok keyrslu -----------#
fc.setFanSpeed(0) #slokkva á viftu
fc.fanOff()
fc.heaterOff()
GPIO.cleanup() # resets all GPIO ports used by this function
