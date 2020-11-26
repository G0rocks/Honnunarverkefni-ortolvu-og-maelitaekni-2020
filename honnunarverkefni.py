# coding=UTF-8
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
import termplotlib                  # Documentation: https://pypi.org/project/termplotlib/ # Athuga hvort hægt sé að setja termplotlib upp á raspberry pi áður en við notum
import threading                    # Documentation: https://docs.python.org/3/library/threading.html # Getum vonandi notað tvo threada til að láta annan þeirra stjórna óskgildinu og hinn vera stýringin okkar
from threading import Thread, local        # Maður þarf að importa með "pip3 install thread6"
import numpy as np                  # Documentation: https://numpy.org/doc/

############ Config ##################
# Project config
projectIsActive = True        # When this value becomes False the run is over and we end the threads, save and exit the program
debugging = True              # When this value is True the pi prints out a lot of text which can be useful for debugging. When false, the raspi only prints out interesting data to let us know the progress

# PID config
P_weight = 0.6 # Vægi P í PID stýringu
I_weight = 0.3 # Vægi I í PID stýringu
D_weight = 0.1 # Vægi D í PID stýringu
K_mognun = 1 # Mögnun (e. amplification) PID stýringar

# GPIO setup
GPIO.setwarnings(False)       # Disable warnings about pin configuration being something other than the default
GPIO.setmode(GPIO.BCM)        # Use Broadcom pinout

# Data config
gogn = np.empty((0,10), float)   # Býr til gagnatöflu með 7 dálkum sem tekur bara við int gildum. Dálkar: [timi,hitastig,duty_cycle,tach_hall_rpm, rakastig, heater_is_on, oskgildi, Error (munur a oskgildi og raunhita), integral, derivative]
TIME_COL = 0; TEMP_COL = 1; DUTY_COL = 2; TACH_COL = 3; HUM_COL = 4; HEATER_ON_COL = 5; OSK_COL = 6; ERR_COL = 7;INT_COL = 8; DER_COL = 9        # Fastar sem innihalda dálkana fyrir hvern lið fyrir sig
maxDeltaT = 0.2     # Hámarks hitamismunur á seinustu mælingu og mælingunni sem var fyrir 10 mælingum til að við skilgreinum okkur við jafnvægi
oskgildi = 20       # Óskgildið sem stýringin reynir að ná. Skilgreint við herbergishitastig og er sett upp síðar.

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
def GPIO_setup_func():
  """
  A function which sets up the GPIO environment correctly
  """
  global FAN_GPIO_PIN
  global TACH_GPIO_PIN
  global RELAY_FAN_GPIO_PIN
  global RELAY_HEATER_GPIO_PIN
  GPIO.setwarnings(False)       # Disable warnings about pin configuration being something other than the default
  GPIO.setmode(GPIO.BCM)        # Use Broadcom pinout
  GPIO.setup(RELAY_FAN_GPIO_PIN, GPIO.OUT, initial=GPIO.HIGH) # HIGH MEANS RELAY IS OFF
  GPIO.setup(FAN_GPIO_PIN, GPIO.OUT, initial=GPIO.LOW)  # Set FAN_GPIO_PIN as output with the initial value GPIO.LOW
  GPIO.setup(TACH_GPIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
  GPIO.setup(RELAY_HEATER_GPIO_PIN, GPIO.OUT, initial=GPIO.HIGH) # HIGH MEANS RELAY IS OFF

def castAsInt(a):
  """
  Function takes in value a and attempts to cast it as int, returns "null" if it fails
  """
  try:
    return int(a)
  except:
    return "null"

def inputDutyCycle():
  """
  Biður notanda um input sem uppfyllir skilyrði til að vera notað sem duty cycle. Skilar int gildi á milli 0 og 100 bæði mörk tekin með
  """
  b = input("Hvaða duty cycle viltu prófa?")
  b = castAsInt(b)
  while (True):   # Safety measure in case somebody puts "Fiskur" as a number
    try:
      while (b == "null" or (castAsInt(b) < 0 or castAsInt(b)>100)):
        print("Sláðu inn heila tölu á milli 0 og 100")
        b = castAsInt(input("Hvaða duty cylce viltu prófa?"))
      break
    except ValueError as ex:
      print('%s\nCan not convert %s to int' % (ex, b))
  return b

def inputLotuFjoldi():
  """
  Biður notanda um fjölda lota til að prófa. Skilar int tölu sem er 0 eða stærri
  """
  print("Ath 1 lota er 5 sek þ.e. 12 lotur mæla í 60 sek")
  c = input("Hversu margar lotur viltu profa?: ")
  c = castAsInt(c)
  while (True):   # Safety measure in case somebody puts "Fiskur" as a number
    try:
      while (c == "null" or castAsInt(c) < 0):
        print("Sláðu inn heila tölu sem er stærri en 0")
        c = castAsInt(input("Hversu margar lotur viltu prófa?"))
      break
    except ValueError as ex:
      print('%s\nCan not convert %s to int' % (ex, c))
  return c

def setFanSpeed(PWM_duty_cycle):
  """
  Sets fan speed to PWM_duty_cycle. Must be between 0 and 100 (both 0 and 100 included)
  """
  global fan_is_on
  global last_duty_cycle
  if fan_is_on:
    if PWM_duty_cycle<0: PWM_duty_cycle=0
    elif PWM_duty_cycle>100: PWM_duty_cycle=100
    fan.start(PWM_duty_cycle)    # set the speed according to the PWM duty cycle
    print("Fan duty cycle: ", PWM_duty_cycle)
    last_duty_cycle = PWM_duty_cycle
  else:
    print("Turn the fan on first")
  return()

def fanOff():
  """
  Turns off the fan
  """
  global fan_is_on
  GPIO.output(RELAY_FAN_GPIO_PIN, GPIO.HIGH)
  fan_is_on = False
  print("Fan off")
  return()

def fanOn():
  """
  Turns on the fan
  """
  global fan_is_on
  GPIO.output(RELAY_FAN_GPIO_PIN, GPIO.LOW)
  fan_is_on = True
  print("Fan on")
  return()

def tach_count(sec,GPIO_PIN):
  """
  Measures how many times an input is received through GPIO_PIN in sec number of seconds
  """
  GPIO.setmode(GPIO.BCM)
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
  global heater_is_on
  GPIO.output(RELAY_HEATER_GPIO_PIN, GPIO.HIGH)
  heater_is_on = False
  if debugging:
    print("Heater off")
  return()

def heaterOn():
  """
  Turns on the heater
  """
  global heater_is_on
  GPIO.output(RELAY_HEATER_GPIO_PIN, GPIO.LOW)
  heater_is_on = True
  if debugging:
    print("Heater on")
  return()

def measureTemp():
  """
  Mælir hitastig beint í breytun 'hitastig'.
  Ef það kemur upp villa við mælingu þá prentast hún út, við bíðum í sensor_cache_clear_time og reynum aftur.
  Hámark 5 sinnum, svo gefumst við upp.
  """
  keepGoing = True
  hitastig = -1
  while (keepGoing):
    try: 
      hitastig = dhtDevice.temperature
      keepGoing = False
    except RuntimeError as error:
        # Villur koma reglulega upp - getur verið erfitt að lesa gildi nemans, bara reyna aftur
        if debugging:
          print(error.args[0])
        time.sleep(sensor_cache_clear_time)
    except Exception as error:
        dhtDevice.exit()
        raise error
  return (hitastig)

def measureHum():
  """
  Mælir og skilar rakastigi.
  Ef það kemur upp villa við mælingu þá prentast hún út, við bíðum í sensor_cache_clear_time og reynum aftur.
  """
  keepGoing = False
  rakastig = 0
  while (keepGoing):
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
  return rakastig

def elapsedTime(UpphafsTimi):
  """
  Mælir hversu langur mikil tími hefur liðið síðan einhver X upphafstimi. 
  """
  nowTimi = time.time()
  Time = nowTimi-UpphafsTimi
  return Time

def is_in_equilibrium(gogn, numCol):
  """
  Tekur inn numpy array gogn og númer dálks numCol sem inniheldur hitastigsmælingar. Athugar hvort að hitamismunur á seinustu mælingu og mælingunni sem var 10 mælingum fyrr sé nógu lítið til að hægt sé að tala um að kerfið sé komið í jafnvægi. Skilar True ef jafnvægi og False ef ekki jafnvægi.
  """
  global maxDeltaT
  numRows = gogn.shape[0]
  if numRows<12:
    return False
  else:
    subgogn = gogn[(numRows-11):(numRows-1), numCol]
    medaltal = np.average(subgogn)
    T2 = gogn[numRows-1][numCol]
    deltaT = T2-medaltal
    print("DeltaT: {:.3f}".format(deltaT))
    print("maxDeltaT: {:.3f}".format(maxDeltaT))
    if (abs(deltaT) <= maxDeltaT):
      return True
    else:
      return False

def get_RPM():
  """
  Fall sem skilar RPM viftu sem float
  """
  global tach_count_time
  global TACH_GPIO_PIN
  return float(tach_count(tach_count_time,TACH_GPIO_PIN))/tach_count_time/2/2*60

def measureAllez(duty_cycle,fjoldi):
  """
  Tekur inn gildi fyrir hvaða duty-cycle viftan á að vera á og hversu margar lotur á að mæla og framkvæmir þann fjölda mælinga á þessu tiltekna duty-cycle
  """ 
  counter = 0
  global gogn
  global STARTTIME
  global heater_is_on
  global oskgildi
  while (counter < fjoldi): # User input akveður fjölda lota
    setFanSpeed(duty_cycle) # viftuhraði settur í gildi sem var slegið inn í upphafi
    hitastig = measureTemp()
    rakastig = measureHum()
    if hitastig != -1:
      timi = elapsedTime(STARTTIME)
      tach_hall_rpm = get_RPM()
      if heater_is_on:
        local_heater_is_on = 1
        print_local_heater_is_on = "on"
      else:
        local_heater_is_on = 0
        print_local_heater_is_on = "off"
      error = oskgildi-hitastig
      if gogn.shape[0] < 2:
        integral = error
        derivative = 0
      else:
        integral = gogn[gogn.shape[0]-1][INT_COL]+error
        derivative = gogn[gogn.shape[0]-1][ERR_COL]-gogn[gogn.shape[0]-2][ERR_COL]
      gogn = np.append(gogn, np.array([[timi,hitastig,duty_cycle,tach_hall_rpm, rakastig, local_heater_is_on, oskgildi, error, integral, derivative]]), axis=0)
      print("Timi: {:.2f}    Hitastig: {:.2f}°C    Duty cycle: {:.2f}%    RPM: {:.2f}    rakastig: {:.2f}%    Hitari (1 = on, 0 = off): {}    Óskgildi: {:.2f}°C"
        .format(timi, hitastig, duty_cycle, tach_hall_rpm, rakastig, print_local_heater_is_on, oskgildi))
      time.sleep(5)
      counter += 1
      np.savetxt('nidurstodur.csv', gogn, delimiter=',', fmt='%d')

def measureAllData(gogn, oskgildi):
  """
  Mælir/athugar [Tími, hitastig, duty_cycle,tach_hall_rpm, rakastig, heater_is_on, oskgildi] og setur inn í gogn fylkið í þessari röð.
  """
  global STARTTIME
  timi = elapsedTime(STARTTIME)
  hitastig = measureTemp()
  global last_duty_cycle
  global fan_is_on
  if fan_is_on:
    local_duty_cycle = last_duty_cycle
  else:
    local_duty_cycle = 0
  tach_hall_rpm = get_RPM()
  rakastig = measureHum()
  global heater_is_on
  if heater_is_on:
    local_heater_is_on = 1
  else:
    local_heater_is_on = 0
  while oskgildi == None:
    sleep(1)
  error = oskgildi-hitastig
  if gogn.shape[0] < 2:
    integral = error
    derivative = 0
  else:
    integral = gogn[gogn.shape[0]-1][INT_COL]+error
    derivative = gogn[gogn.shape[0]-1][ERR_COL]-gogn[gogn.shape[0]-2][ERR_COL]
  gogn = np.append(gogn, np.array([[timi,hitastig,local_duty_cycle,tach_hall_rpm, rakastig, local_heater_is_on, oskgildi, error, integral, derivative]]), axis=0)

def oskgildi_setup():
  """
  Fall sem gerir mælingar á 10% og 90% duty cycle og finnur hitastig sem er miðgildið og skilar því
  """
  print("Set upp upphafsóskgildi")
  global oskgildi
  global gogn
  """
  gogn_local = np.empty((0,3), float)
  try:
    heaterOn()
    sleep(20)
    fanOn()
    local_duty_cycle = 10
    setFanSpeed(local_duty_cycle)
    sleep(10)
    hitastig = measureTemp()
    gogn_local = np.append(gogn_local, np.array([[hitastig, elapsedTime(STARTTIME), local_duty_cycle]]), axis=0)
    while (not(is_in_equilibrium(gogn_local, 0))):
      hitastig = measureTemp()
      if hitastig != -1:
        gogn_local = np.append(gogn_local, np.array([[hitastig, elapsedTime(STARTTIME), local_duty_cycle]]), axis=0)
        sleep(2)
        # print("gogn_local: \n", gogn_local)
    T1 = gogn_local[gogn_local.shape[0]-1][0]
    print("T1: ", T1)
    # Vista gogn_local
    np.savetxt('oskgildi1.csv', gogn_local, delimiter=',', fmt='%d')
    # Reset gogn_local
    gogn_local = np.empty((0,3), float)
    local_duty_cycle = 90
    setFanSpeed(local_duty_cycle)
    sleep(30)
    while (not(is_in_equilibrium(gogn_local, 0))):
      hitastig = measureTemp()
      if hitastig != -1:
        gogn_local = np.append(gogn_local, np.array([[hitastig, elapsedTime(STARTTIME), local_duty_cycle]]), axis=0)
        sleep(2)
    T2 = gogn_local[gogn_local.shape[0]-1][0]
    print("T2: ", T2)
    oskgildi = (T1+T2)/2
    print("upphafsóskgildi: ", oskgildi)
    np.savetxt('oskgildi2.csv', gogn_local, delimiter=',', fmt='%d')
    return oskgildi
  # trap a CTRL+C keyboard interrupt
  except KeyboardInterrupt:
    setFanSpeed(FAN_OFF)
    GPIO.cleanup() # resets all GPIO ports used by this function
  """
  oskgildi = 23.5
  print("Upphafsóskgildi er: ", oskgildi)

def geraGraf():
  """
  Gerum graf til þess að skoða niðurstöður og vistum það í skránna nstGraf.png
  """
  """
  x = gogn[0:1] # geymir upplysingar um tima
  heat = gogn[1:2]
  duty = gogn[2:3]
  rpm = gogn[3:4]
  """

  """
  fig, axs = plt.subplots(3)
  fig.suptitle('Niðurstöður Mælinga')
  axs[0].plot(x, rpm)
  axs[0].set_title("Viftuhraði")
  axs[1].plot(x, duty)
  axs[1].set_title("Duty cycle")
  axs[2].plot(x, heat)
  axs[2].set_title("Hiti")
  plt.legend()
  plt.savefig('nstGraf.png')
  """

############################################################################################
#################################### Threads ##########################################
def oskgildi_thread_func(projectIsActive, oskgildi, UPPHAFSOSKGILDI, gogn):
  """
  Þráður sem sér um að stjórna óskgildinu eins og notandi. Byrjar þegar búið er að skilgreina upphafsóskgildi. Tekur inn projectIsActive, oskgildi og UPPHAFSOSKGILDI
  """
  print("Óskgildi thread start")
  oskgildi = UPPHAFSOSKGILDI
  try:
    # Thread starts when oskgildi_setup() has been run
    # Liður 1
    # Ná jafnvægi í UPPHAFSOSKGILDI
    while projectIsActive:
      if debugging:
        print("Osk loop1")
      if is_in_equilibrium(gogn, 1):
        break
      sleep(10*sensor_cache_clear_time)

      # Liður 2
    oskgildi = 50
    # Ná jafnvægi í 50°C
    while projectIsActive:
      if debugging:
        print("Osk loop2")
      if is_in_equilibrium(gogn, 1):
        break
      sleep(10*sensor_cache_clear_time)
    # Vaxa línulega frá 50°C upp í 60°C á 30 sek
    local_start_time = time.time()
    while projectIsActive and elapsedTime(local_start_time) < 30:
      if debugging:
        print("Osk loop3")
      oskgildi = oskgildi+1/30
      if oskgildi <= 60:
        break
      sleep(0.1)
    oskgildi = 60     # Til öryggis ef það var ekki akkúrat 60°C
    # Halda óskgildi óbreyttu í 30 sek
    sleep(30)
    # Lækka óskgildi línulega frá 60°C niður í 40°C á 30 sek
    local_start_time = time.time()
    while projectIsActive and elapsedTime(local_start_time) < 30:
      if debugging:
        print("Osk loop4")
      oskgildi = oskgildi-2/30
      if oskgildi >= 40:
        break
      sleep(0.1)
    oskgildi = 40   # Til öryggis ef það var ekki akkúrat 40°C
    # Ná jafnvægi í 40°C
    while projectIsActive:
      if is_in_equilibrium():
        break
    sleep(sensor_cache_clear_time)

    projectIsActive = False   # Set to False when second part of exercise is over

  # trap a CTRL+C keyboard interrupt
  except KeyboardInterrupt:
    projectIsActive = False # Stöðva verkefnið
    setFanSpeed(FAN_OFF)
    GPIO.cleanup() # resets all GPIO ports used by this function

def styring_thread_func(projectIsActive, gogn):
  """
  Þráður sem sér um að reyna að láta hitastigið sem neminn nemur fylgja óskgildinu.
  """
  print("Styring thread start")
  global P_weight
  global I_weight
  global D_weight
  global K_mognun
  while gogn.shape[0] < 2:
    print("Waiting for data")
    sleep(10*sensor_cache_clear_time)
  while(projectIsActive):
    print("Styring loop")
    try:
      # PID stýring - Módel
      # Inntak
      lastRow = gogn.shape[0]-1
      error_signal = gogn[lastRow, ERR_COL]

      # P hluti
      P_value = error_signal

      # I hluti
      I_value = gogn[lastRow, INT_COL]

      # D hluti
      D_value = gogn[lastRow, DER_COL]

      # Úttak
      control_signal = K_mognun*( P_value*P_weight+I_value*I_weight+D_value*D_weight )
      print("Control signal: ", control_signal)

      # Stýring
      if control_signal < 0:
        fanOn()
        heaterOff()
        if control_signal < -1:
          setFanSpeed(25)
        elif control_signal < -2:
          setFanSpeed(50)
        elif control_signal < -3:
          setFanSpeed(75)
        elif control_signal < -4:
          setFanSpeed(100)
      elif control_signal > 0:
        fanOff()
        heaterOn()
      sleep(2*sensor_cache_clear_time)

    # trap a CTRL+C keyboard interrupt
    except KeyboardInterrupt:
      setFanSpeed(FAN_OFF)
      GPIO.cleanup() # resets all GPIO ports used by this function

    # If something unexpected happens
    except Exception as error:
      if debugging:
        print(error.args[0])
      time.sleep(sensor_cache_clear_time)


def Measure_thread_func(projectIsActive, gogn, oskgildi):
  """
  Þráður sem mælir gögn endalaust og stingur inn í gogn fylkið á meðan projectIsActive breytan skilar True og prentar út stöðu mála.
  """
  print("Measurement thread start")
  fig = termplotlib.figure()
  while(projectIsActive):
    try:
      lastRow = gogn.shape[0]-1
      measureAllData(gogn, oskgildi)
      if lastRow >= 0:
        print("{} Temp: {:.2f}   Error: {:.2f}    Integral: {:.2f}    Derivative: {:.2f}".format(lastRow, gogn[lastRow][TEMP_COL], gogn[lastRow][ERR_COL], gogn[lastRow][INT_COL], gogn[lastRow][DER_COL]))
        sleep(0.5)
        if lastRow > 10:
          x = np.linspace(gogn[lastRow-10][TIME_COL] ,gogn[lastRow][TIME_COL] , 10)   # fylki sem fer í 10 jöfnum skrefum yfir seinustu 10 tímapunkta
          y = np.linspace(gogn[lastRow-10][ERR_COL] ,gogn[lastRow][ERR_COL] ,10)  # Samsvarandi Error values fyrir tímann á x-ás
          fig.plot(x, y, label ="data", width=50, height=15)
          fig.show()
    except RuntimeError as error:
      # Villur koma reglulega upp - getur verið erfitt að lesa gildi nemans, bara reyna aftur
      print(error.args[0])
      time.sleep(sensor_cache_clear_time)
    except Exception as error:
      print(error.args[0])
      time.sleep(sensor_cache_clear_time)
    sleep(sensor_cache_clear_time)

############################################################################################
#################################### Main program ##########################################
STARTTIME = time.time() #Stilla upphafstima
# UPPHAFSRAKASTIG = measureHum()
# UPPHAFSHITASTIG = measureTemp()
UPPHAFSOSKGILDI = oskgildi_setup()

oskgildi_thread = threading.Thread(target=oskgildi_thread_func, args=(projectIsActive,oskgildi,UPPHAFSOSKGILDI, gogn))
styring_thread = threading.Thread(target=styring_thread_func, args=(projectIsActive, gogn))
measure_thread = threading.Thread(target=Measure_thread_func, args=(projectIsActive, gogn, oskgildi))

"""
print("____Yfirfærslufall profun____")
b = inputDutyCycle()
c = inputLotuFjoldi()

# Búum til tóm fylki og vistum gildi í þau. Notaðu til að halda utan um gögn
# Notum NumPy array til þess að geta vistað sem .csv og einfaldað vinnslu á gögnum
# Ath. seinna talan er vídd fylkis og þarf að aðalaga hana að því hversu margar breytur á að geyma
# gogn = np.empty((0,4), int)


counter = 0

# Tökum mælingu og vistum gögn í nidurstodur.csv
try :
  if c > 0:
    heaterOn()
    fanOn()
    measureAllez(b,c)
    print("True ef þetta virkaði:", is_in_equilibrium(gogn,1))
    ##### measureAllez(20,c)
    # Save 2D numpy array to csv file
  # np.savetxt('nidurstodur.csv', gogn, delimiter=',', fmt='%d') 
  # try :
  #   STARTTIME = time.time() #Stilla upphafstima
  #   heaterOn()
  #   fanOn()
    # while (counter < c): # User input akveður fjölda lota
    #   duty_cycle = b
    #   setFanSpeed(duty_cycle) # viftuhraði settur í gildi sem var slegið inn í upphafi
    #   hitastig = measureTemp() 
    #   timi = elapsedTime(STARTTIME)
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

geraGraf()
"""

oskgildi_thread.start()
measure_thread.start()
styring_thread.start()

while projectIsActive:
  sleep(10)

np.savetxt('nidurstodur.csv', gogn, delimiter=',', fmt='%d')
print("Gögn vistuð sem \'nidurstodur.csv\'")
print("Cleanup")
# reset all GPIO ports used. Important in order to prevent accidental fire hazards
fanOff()
heaterOff()
GPIO.cleanup()