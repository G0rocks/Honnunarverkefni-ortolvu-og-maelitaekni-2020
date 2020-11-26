# coding=UTF-8

############ Import modules ##################
from time import sleep
import RPi.GPIO as GPIO             # Documentation: https://sourceforge.net/p/raspberry-gpio-python/wiki/Home/
import time                         # Documentation: https://docs.python.org/3/library/time.html
import datetime                     # Documentation: https://docs.python.org/3/library/datetime.html
import board                        # Documentation: https://pypi.org/project/board/
import adafruit_dht                 # Documentation: https://circuitpython.readthedocs.io/projects/dht/en/latest/#
import matplotlib.pyplot as plt     # Documentation: https://matplotlib.org/api/pyplot_api.html
# import termplotlib                  # Documentation: https://pypi.org/project/termplotlib/ # Athuga hvort hægt sé að setja termplotlib upp á raspberry pi áður en við notum
import threading                    # Documentation: https://docs.python.org/3/library/threading.html # Getum vonandi notað tvo threada til að láta annan þeirra stjórna óskgildinu og hinn vera stýringin okkar
from threading import Thread        # Maður þarf að importa með "pip3 install thread6"
import numpy as np                  # Documentation: https://numpy.org/doc/
############ Config ##################
# Set project to active
#projectIsActive = True        # When this value becomes False the run is over and we end the threads, save and exit the program

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
fan = GPIO.PWM(FAN_GPIO_PIN,PWM_FREQ)                 # create a PWM instance called fan
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

def setFanSpeed(PWM_duty_cycle):
  """
  Sets fan speed to PWM_duty_cycle. Must be between 0 and 100 (both 0 and 100 included)
  """
  #GPIO.output(RELAY_FAN_GPIO_PIN, GPIO.LOW)
  if PWM_duty_cycle<0: PWM_duty_cycle=0
  elif PWM_duty_cycle>100: PWM_duty_cycle=100
  try:
    fan.start(PWM_duty_cycle)    # set the speed according to the PWM duty cycle
    print("Fan duty cycle: {:.1f}".format(PWM_duty_cycle))
  except:
    print("error setting fan duty cycle")

def fanOff():
  """
  Turns off the fan
  """
  try:
    GPIO.output(RELAY_FAN_GPIO_PIN, GPIO.HIGH)
    print("Fan off")
  except:
    print("error turning fan off")

def fanOn():
  """
  Turns on the fan
  """
  try:
    GPIO.output(RELAY_FAN_GPIO_PIN, GPIO.LOW)
    print("Fan on")
  except:
    print("error turning fan on")

def heaterOff():
  """
  Turns off the heater
  """
  try:
    GPIO.output(RELAY_HEATER_GPIO_PIN, GPIO.HIGH)
    print("Heater off")
  except:
    print("error turning heater off")

def heaterOn():
  """
  Turns on the heater
  """
  try:
    GPIO.output(RELAY_HEATER_GPIO_PIN, GPIO.LOW)
    print("Heater on")
  except:
    print("Error turning heater on ")

def measureTemp():
  """
  Mælir hitastig beint í breytun 'hitastig'.
  Ef það kemur upp villa við mælingu þá prentast hún út, við bíðum í sensor_cache_clear_time og reynum aftur.
  Hámark 5 sinnum, svo gefumst við upp.
  """
  keepGoing = True
  hitastig = -1
  while keepGoing:
    try: 
      hitastig = dhtDevice.temperature
      if (hitastig > 0) and hitastig is not None:
        keepGoing = False
      if (hitastig < 0):
        keepGoing = True
    except:
      time.sleep(2)
      continue
  return (hitastig)

def elapsedTime(UpphafsTimi):
  """
  Mælir hversu langur mikil tími hefur liðið síðan einhver X upphafstimi. 
  """
  nowTimi = time.time()
  Time = nowTimi-UpphafsTimi
  return Time

def is_in_equilibrium(gogn, numCol, maxDeltaT):
  """
  Tekur inn numpy array gogn og númer dálks numCol sem inniheldur hitastigsmælingar. Athugar hvort að hitamismunur á seinustu mælingu og mælingunni sem var 10 mælingum fyrr sé nógu lítið til að hægt sé að tala um að kerfið sé komið í jafnvægi. Skilar True ef jafnvægi og False ef ekki jafnvægi.
  """
  numRows = gogn.shape[0]
  if numRows<20:
    return False
    # T1 = gogn[0][numCol]
  else:
    #print(numRows)
    deltaT = np.average(gogn[(numRows-9):(numRows), numCol]) - np.average(gogn[(numRows-19):(numRows-10), numCol])
    #print("DeltaT: {:.3f}".format(deltaT))
    #print("maxDeltaT: {:.3f}".format(maxDeltaT))
    if (abs(deltaT) <= maxDeltaT):
      return True
    else:
      return False

def equilibrium_control(gogn, maxDeltaT):
  """
  Tekur inn numpy array gogn og númer dálks numCol sem inniheldur hitastigsmælingar. Athugar hvort að hitamismunur á seinustu mælingu og mælingunni sem var 10 mælingum fyrr sé nógu lítið til að hægt sé að tala um að kerfið sé komið í jafnvægi. Skilar True ef jafnvægi og False ef ekki jafnvægi.
  """
  numRows = gogn.shape[0]
  oskgildi = gogn[(numRows-1), 5]
  if numRows<20:
    return False
    # T1 = gogn[0][numCol]
  else:
    #print(numRows)
    deltaT = np.average(gogn[(numRows-9):(numRows), 1]) - oskgildi
    #print("DeltaT: {:.3f}".format(deltaT))
    #print("maxDeltaT: {:.3f}".format(maxDeltaT))
    if (abs(deltaT) <= maxDeltaT):
      return True
    else:
      return False


def control(gogn):
  """
  tekur inn [tími, hitastig, fan_on, duty_cycle, heater_on, oskgildi, error, sum_error] og skilar control value
  """
  numRows = gogn.shape[0]

  K = 30
  
  #T_I = 1000
  T_D = 5
  if (numRows < 2):
    T = 1000
    prev_err = 0
  else:
    T = gogn[(numRows-1), 0] - gogn[(numRows-2), 1]
    prev_err = gogn[(numRows-2), 6]
  
  err = gogn[(numRows-1), 6]
  #sum_err = gogn[(numRows-1), 7]

  ctrl = K*(err + T_D/T * (err-prev_err))
  return(ctrl)


def operate(gogn, control_signal):
  """
  Tekur inn control value og stýrir kerfinu eftir því
  """
  numRows = gogn.shape[0]
  duty_cycle = gogn[(numRows-1), 3]
  fan_on = gogn[(numRows-1), 2]
  # Stýring
  if control_signal > 0:
    
    #heaterOff()
    duty_cycle += control_signal

    if (duty_cycle > 100):
      duty_cycle = 100
    elif (duty_cycle < 0):
      duty_cycle = 0
    
    if (not(fan_on)):
      fanOn()
      fan_on = True
    setFanSpeed(duty_cycle)

  elif (control_signal < 0):
    duty_cycle = 0
    fanOff()
    fan_on = False
    #heaterOn()

  return(fan_on, duty_cycle)

def oskgildi(slope_start, nowTime, equil_count):
  """
  Fall sem ákvarðar óskgildi
  """
  if (equil_count == 0):
    osk = 23.3
  elif (equil_count == 1):
    osk = 50 
  elif (equil_count > 1):
    duration = nowTime - slope_start
    if (duration < 30):
      osk = 50 + duration * 1/3
    elif ((30 <= duration) and (duration <60)):
      osk = 60
    elif ((60 <= duration) and (duration <90)):
      osk = 60 - (duration-60) * 2/3
    elif (duration > 90):
      osk = 40
  
  return(osk)

