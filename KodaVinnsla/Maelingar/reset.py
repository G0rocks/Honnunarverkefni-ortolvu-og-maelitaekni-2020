# coding=UTF-8

############ Import modules ##################

import function_config as fc
from time import sleep
import RPi.GPIO as GPIO             # Documentation: https://sourceforge.net/p/raspberry-gpio-python/wiki/Home/
import time                         # Documentation: https://docs.python.org/3/library/time.html
import datetime                     # Documentation: https://docs.python.org/3/library/datetime.html
import board                        # Documentation: https://pypi.org/project/board/
import adafruit_dht                 # Documentation: https://circuitpython.readthedocs.io/projects/dht/en/latest/#
import matplotlib.pyplot as plt     # Documentation: https://matplotlib.org/api/pyplot_api.html

# GPIO setup
GPIO.setwarnings(False)       # Disable warnings about pin configuration being something other than the default
GPIO.setmode(GPIO.BCM)        # Use Broadcom pinout

# Data config
#gogn = np.empty((0,7), float)   # Býr til gagnatöflu með 7 dálkum sem tekur bara við int gildum. Dálkar: [timi,hitastig,duty_cycle,tach_hall_rpm, rakastig, heater_is_on, oskgildi]
#maxDeltaT = 0.2     # Hámarks hitamismunur á seinustu mælingu og mælingunni sem var fyrir 10 mælingum til að við skilgreinum okkur við jafnvægi
#oskgildi = 20       # Óskgildið sem stýringin reynir að ná. Skilgreint við herbergishitastig og er sett upp síðar.

# Fan config
FAN_GPIO_PIN = 20       # BCM pin used to drive PWM fan
PWM_FREQ = 25000        # [Hz] 25kHz for PWM control
PWM_OFF = 0             # the PWM_duty_cycle 0%
PWM_MAX = 100           # the PWM_duty_cycle 100%
TACH_GPIO_PIN = 21      # BCM pin for reading the tachometer
tach_count_time = 2          # seconds for counting sensor changes
fan_is_on = False       # Boolean variable. False if fan is off and True if fan is on
FAN_OFF=PWM_OFF         # If no relay connection, this sets the fan speed to the lowest setting (230 RPM - https://www.arctic.ac/en/F12-PWM/AFACO-120P2-GBA01). If relay connection, use the relay to cut the power to the fan to turn it off.
last_duty_cycle = 0     # Used to know what the last duty cycle set was in order to input the value to gogn
# Setting up relay for FAN
RELAY_FAN_GPIO_PIN = 26         # BCM pin used to turn RELAY for FAN ON/OFF
GPIO.setup(RELAY_FAN_GPIO_PIN, GPIO.OUT, initial=GPIO.HIGH) # HIGH MEANS RELAY IS OFF

# PWM used to control the fan's speed
GPIO.setup(FAN_GPIO_PIN, GPIO.OUT, initial=GPIO.LOW)  # Set FAN_GPIO_PIN as output with the initial value GPIO.LOW
#fan = GPIO.PWM(FAN_GPIO_PIN,PWM_FREQ)                 # create a PWM instance called fan
# tachometer - from a hall sensor located in the fan
GPIO.setup(TACH_GPIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Setting up relay for Heater
RELAY_HEATER_GPIO_PIN = 16  # BCM pin used to turn RELAY for HEATER ON/OFF
GPIO.setup(RELAY_HEATER_GPIO_PIN, GPIO.OUT, initial=GPIO.HIGH) # HIGH MEANS RELAY IS OFF
heater_is_on = False       # Boolean variable. False if heater is off and True if heater is on

# Sensor config
sensor_cache_clear_time = 2 # Hversu langan tíma við þurfum að bíða eftir því að mælirinn tæmi minnið sitt ef hann nær ekki að mæla (a.m.k. 2 sekúndur)
dhtDevice = adafruit_dht.DHT22(board.D5)
UPPHAFSHITASTIG = 0 # Upphafshitastig
hitastig = 0  # Breyta til að fylgjast með hitastigi
deltaT = 0 # breyta til að fylgjast með breyting á hitastigi
UPPHAFSRAKASTIG = 0 # Upphafsrakastig
rakastig = 0 # breyta til að fylgjast með rakastigi
deltaH = 0 # Breyta til að fylgjast með breytingu á rakastigi (e. humidity)

############ Define functions ##################


#----------- Núllstilla viftu og hitara í lok keyrslu -----------#
fc.setFanSpeed(0) #slokkva á viftu
fc.fanOff()
fc.heaterOff()
GPIO.cleanup() # resets all GPIO ports used by this function
