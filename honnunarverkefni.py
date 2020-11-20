"""
Hönnunarverkefni - Haust 2020
Lokaverkefni í áfanganum Örtölvu og mælitækni við HÍ.
Höfundar: Benedikt, Huldar, Ísak og Rúnar

Verkefnalýsing:
https://haskoliislands.instructure.com/courses/1144/assignments/10160
Í verkefninu á að hanna, útfæra og prófa stýringu fyrir véleindakerfi. Véleindakerfið er samsett af kerfi sem á að stýra (hitastig í rými), nema (hitanema), hreyfli (hitagjafa og viftu) og tölvu. Kröfurnar eru að kerfið sé stöðugt (mögnunaröryggi a.m.k. 2)  og geti haldið stöðugu óskgildi og brugðist við breytingum í óskgildi eins og lýst er hér fyrir neðan á sem bestan hátt hvað varðar hraða, skekkju í jafnvægi, næmni gagnvart truflunum og breytileika og stýrimerki.

1. Mælið hitastig við efri og neðri mörk línulega sviðs viftunar (u.þ.b. 10% og 90% af duty cycle) með hitagjafann í gangi. Veljið sem óskgildi hitastigið sem er mitt á milli þessara gilda.
2. Breytið óskgildi í 50°C. Eftir að hafa náð jafvægi við 50°C breytist óskgildi á eftirfarandi hátt:
  1. Hækkar línulega um 10°C í 30 sek 
  2. Óbreytt í 30 sek
  3. Lækkar línulega um 20°C í 30 sek

Gagnlegar demo skrár: PWM_demo.py hall_sensor_demo.py RELAY_test.py
"""

############ Import modules ##################
from time import sleep
import RPi.GPIO as GPIO             # Documentation: https://sourceforge.net/p/raspberry-gpio-python/wiki/Home/
import time                         # Documentation: https://docs.python.org/3/library/time.html
import datetime                     # Documentation: https://docs.python.org/3/library/datetime.html
import board                        # Documentation: https://pypi.org/project/board/
import adafruit_dht                 # Documentation: https://circuitpython.readthedocs.io/projects/dht/en/latest/#
import matplotlib.pyplot as plt     # Documentation: https://matplotlib.org/api/pyplot_api.html
# import termplotlib                  # Documentation: https://pypi.org/project/termplotlib/ # Athuga hvort hægt sé að setja termplotlib upp á raspberry pi áður en við notum
#import threading                    # Documentation: https://docs.python.org/3/library/threading.html # Getum vonandi notað tvo threada til að láta annan þeirra stjórna óskgildinu og hinn vera stýringin okkar
#from threading import thread
import numpy as np                  # Documentation: 
############ Config ##################
# GPIO setup
GPIO.setwarnings(False)       # Disable warnings about pin configuration being something other than the default
GPIO.setmode(GPIO.BCM)        # Use Broadcom pinout

# Fan config
FAN_GPIO_PIN = 20       # BCM pin used to drive PWM fan
PWM_FREQ = 25000        # [Hz] 25kHz for PWM control
PWM_OFF = 0             # the PWM_duty_cycle 0%
PWM_MAX = 100           # the PWM_duty_cycle 100%
TACH_GPIO_PIN = 21      # BCM pin for reading the tachometer
tach_count_time = 2          # seconds for counting sensor changes
fan_is_on = False       # Boolean variable. False if fan is off and True if fan is on
FAN_OFF=PWM_OFF         # If no relay connection, this sets the fan speed to the lowest setting (230 RPM - https://www.arctic.ac/en/F12-PWM/AFACO-120P2-GBA01). If relay connection, use the relay to cut the power to the fan to turn it off.
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

gogn = np.empty((0,4), int)

############ Define functions ##################
def setFanSpeed(PWM_duty_cycle):
  """
  Sets fan speed to PWM_duty_cycle. Must be between 0 and 100 (both 0 and 100 included)
  """
  if fan_is_on:
    fan.start(PWM_duty_cycle)    # set the speed according to the PWM duty cycle
  else:
    print("Turn the fan on first")
  return()

def fanOff():
  """
  Turns off the fan
  """
  GPIO.output(RELAY_FAN_GPIO_PIN, GPIO.LOW)
  fan_is_on = False
  print("Fan off")
  return()

def fanOn():
  """
  Turns on the fan
  """
  GPIO.output(RELAY_FAN_GPIO_PIN, GPIO.HIGH)
  fan_is_on = True
  print("Fan on")
  return()

def tach_count(sec,GPIO_PIN):
  """
  Measures how many times an input is received through GPIO_PIN in sec number of seconds
  """
  duration = datetime.timedelta(seconds=sec)      # measure for one second
  end_time = (datetime.datetime.now()+duration)   # set the time when to stop
  current_pin_status = GPIO.input(GPIO_PIN)
  last_pin_status = 2
  counter = 0
  while ( datetime.datetime.now() < end_time):
    current_pin_status=GPIO.input(GPIO_PIN)
    if (current_pin_status != last_pin_status):
      # print(current_pin_status)
      last_pin_status = current_pin_status
      counter += 1
  return (counter)

def heaterOff():
  """
  Turns off the heater
  """
  GPIO.output(RELAY_HEATER_GPIO_PIN, GPIO.LOW)
  heater_is_on = False
  print("Heater off")
  return()

def heaterOn():
  """
  Turns on the heater
  """
  GPIO.output(RELAY_HEATER_GPIO_PIN, GPIO.HIGH)
  heater_is_on = True
  print("Heater on")
  return()

def measureTemp():
  """
  Mælir hitastig beint í breytun 'hitastig'.
  Ef það kemur upp villa við mælingu þá prentast hún út, við bíðum í sensor_cache_clear_time og reynum aftur.
  Hámark 5 sinnum, svo gefumst við upp.
  """
  keepGoing = True
  loopCounter = 0
  hitastig = -1
  while (keepGoing and loopCounter < 5):
    try: 
      hitastig = dhtDevice.temperature
      keepGoing = False
    except RuntimeError as error:
        # Villur koma reglulega upp - getur verið erfitt að lesa gildi nemans, bara reyna aftur
        print(error.args[0])
        time.sleep(sensor_cache_clear_time)
    except Exception as error:
        dhtDevice.exit()
        raise error
    loopCounter += 1
  return (hitastig)

def measureHum():
  """
  Mælir rakastig beint í breytuna 'rakastig'.
  Ef það kemur upp villa við mælingu þá prentast hún út, við bíðum í sensor_cache_clear_time og reynum aftur.
  Hámark 5 sinnum, svo gefumst við upp.
  """
  keepGoing = True
  loopCounter = 0
  while (keepGoing and loopCounter < 5):
    try: 
      rakastig = dhtDevice.humidity
      keepGoing = False
    except RuntimeError as error:
        # Villur koma reglulega upp - getur verið erfitt að lesa gildi nemans, bara reyna aftur
        print(error.args[0])
        time.sleep(sensor_cache_clear_time)
    except Exception as error:
        dhtDevice.exit()
        raise error
    loopCounter += 1

def elapsedTime(UpphafsTimi):
  """
  Mælir hversu langur mikil tími hefur liðið síðan einhver X upphafstimi. 
  """
  nowTimi = time.time()
  Time = nowTimi-UpphafsTimi
  return Time

def measureAllez(hradi,fjoldi,gogn):
  """
  Tekur inn gildi fyrir hvaða duty-cycle viftan á að vera á og hversu margar lotur á að mæla 
  """
  counter = 0
  while (counter < fjoldi): # User input akveður fjölda lota
    duty_cycle = hradi
    setFanSpeed(duty_cycle) # viftuhraði settur í gildi sem var slegið inn í upphafi
    hitastig = measureTemp() 
    timi = elapsedTime(startTime)
    tach_hall_rpm = float(tach_count(tach_count_time,TACH_GPIO_PIN))/tach_count_time/2/2*60
    gogn = np.append(gogn, np.array([[timi,hitastig,duty_cycle,tach_hall_rpm]]), axis=0)
    print("Hitastig: {:.2f}°C    Timi: {:.2f}     RPM: {:.2f} RPM    Duty cycle: {:.2f}%"
      .format(hitastig,timi,tach_hall_rpm,duty_cycle))
    time.sleep(5)
    counter += 1

############################################################################################
#################################### Main program ##########################################
UPPHAFSRAKASTIG = measureHum()
UPPHAFSHITASTIG = measureTemp()

print("____Yfirfærslufall profun____")
b = int(input("Hvaða duty cycle viltu profa?: "))
print("Ath 1 lota er 5 sek þ.e. 12 lotur mæla í 60 sek")
c = int(input("Hversu margar lotur viltu profa?: "))
# print("Hversu mörg duty cycle viltu prófa?")
# a = int(input("Fjöldi duty cylce: "))
# while (True):   # Safety measure in case somebody puts "Fiskur" as the number of duty cycles
#   try:
#     while (int(a) < 1 ):
#       print("Sláðu inn heila tölu sem er stærri en 0")
#       a = int(input("Fjöldi duty cylce: "))
#     break
#   except ValueError as ex:
#     print('%s\nCan not convert %s to int' % (ex, a))

# Búum til tóm fylki og vistum gildi í þau. Notaðu til að halda utan um gögn
# Notum NumPy array til þess að geta vistað sem .csv og einfaldað vinnslu á gögnum
# Ath. seinna talan er vídd fylkis og þarf að aðalaga hana að því hversu margar breytur á að geyma
# gogn = np.empty((0,4), int)

counter = 0

# Tökum mælingu og vistum gögn í nidurstodur.csv
try :
  startTime = time.time() #Stilla upphafstima
  heaterOn()
  fanOn()
  measureAllez(b,c,gogn)
  measureAllez(80,c,gogn)
  # Save 2D numpy array to csv file
  np.savetxt('nidurstodur.csv', gogn, delimiter=',', fmt='%d') 
# try :
#   startTime = time.time() #Stilla upphafstima
#   heaterOn()
#   fanOn()
  # while (counter < c): # User input akveður fjölda lota
  #   duty_cycle = b
  #   setFanSpeed(duty_cycle) # viftuhraði settur í gildi sem var slegið inn í upphafi
  #   hitastig = measureTemp() 
  #   timi = elapsedTime(startTime)
  #   tach_hall_rpm = float(tach_count(tach_count_time,TACH_GPIO_PIN))/tach_count_time/2/2*60
  #   gogn = np.append(gogn, np.array([[timi,hitastig,duty_cycle,tach_hall_rpm]]), axis=0)
  #   print("Hitastig: {:.2f}°C    Timi: {:.2f}     RPM: {:.2f} RPM    Duty cycle: {:.2f}%"
  #     .format(hitastig,timi,tach_hall_rpm,duty_cycle))
  #   time.sleep(5)
  #   counter += 1
  #   # Save 2D numpy array to csv file
  #   np.savetxt('nidurstodur.csv', gogn, delimiter=',', fmt='%d')

# trap a CTRL+C keyboard interrupt
except KeyboardInterrupt:
  setFanSpeed(FAN_OFF)
  GPIO.cleanup() # resets all GPIO ports used by this function

# Gerum graf til þess að skoða niðurstöður
x = gogn[0:1] # geymir upplysingar um tima
heat = gogn[1:2]
duty = gogn[2:3]
RPM = gogn[3:4]

fig, axs = plt.subplots(3)
fig.suptitle('Niðurstöður Mælinga')
axs[0].plot(x, RPM)
axs[0].set_title("Viftuhraði")
axs[1].plot(x, duty)
axs[1].set_title("Duty cycle")
axs[2].plot(x, heat)
axs[2].set_title("Hiti")
plt.legend()
plt.savefig('nstGraf.png')

# reset all GPIO ports used. Important in order to prevent accidental fire hazards
fanOff()
heaterOff()
GPIO.cleanup()
