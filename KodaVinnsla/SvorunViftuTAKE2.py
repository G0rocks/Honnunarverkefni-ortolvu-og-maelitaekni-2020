import RPi.GPIO as GPIO
import time
import datetime
import matplotlib.pyplot as plt

# Configuration
FAN_GPIO_PIN = 20       # BCM pin used to drive PWM fan
PWM_FREQ = 25000        # [Hz] 25kHz for PWM control

PWM_OFF = 0             # the PWM_duty_cycle 0%
PWM_MAX = 100           # the PWM_duty_cycle 100%

TACH_GPIO_PIN = 21      # BCM pin for reading the tachometer
count_time = 2          # seconds for counting sensor changes

RELAY_FAN_GPIO_PIN = 26 # BCM pin used to turn RELAY for FAN ON/OFF

############ skilgreinum ##################
# Stilla viftuhraða
def setFanSpeed(PWM_duty_cycle):
  fan.start(PWM_duty_cycle)    # set the speed according to the PWM duty cycle
  return()

################################################

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
####
print("Hversu mörg duty cycle viltu prófa?")
a = int(input("Fjöldi duty cylce:"))

########
try:
  GPIO.setwarnings(False)
  GPIO.setmode(GPIO.BCM)
  # PWM notað til að stýra viftuhraða
  GPIO.setup(FAN_GPIO_PIN, GPIO.OUT, initial=GPIO.LOW)
  fan = GPIO.PWM(FAN_GPIO_PIN,PWM_FREQ)
  setFanSpeed(PWM_OFF)
  # tachometer - from a hall sensor located in the fan
  GPIO.setup(TACH_GPIO_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

  # Setting up relay for FAN
  GPIO.setup(RELAY_FAN_GPIO_PIN, GPIO.OUT, initial=GPIO.LOW) # HIGH MEANS RELAY IS OFF

  counter= 0

  ###Búum til tóm fylki og vistum gildi í þau. Notaðu seinna í grafi ##
  Cycle_duty = []
  RPM_Hall = []
  ##############################################

  while (counter < a):
    duty_cycle = PWM_MAX*counter/(a-1)
    Cycle_duty.append(duty_cycle)
    setFanSpeed(duty_cycle)
    time.sleep(4)
    print("Duty cycle: {:.2f}%".format(duty_cycle))
    tach_hall_rpm = float(tach_count(count_time,TACH_GPIO_PIN))/count_time/2/2*60
    RPM_Hall.append(tach_hall_rpm)
    print("Hall RPM: {:.2f} RPM".format(tach_hall_rpm))
    counter += 1

# trap a CTRL+C keyboard interrupt
except KeyboardInterrupt:
  setFanSpeed(FAN_OFF)
  GPIO.cleanup() # resets all GPIO ports used by this function

###Gerum graf af duty cycle sem fall af RPM fyrir báða skynjara
###############################################################
a = plt.plot(Cycle_duty,RPM_Hall,label= "Hall skynjari")
plt.xlabel("Duty Cycle")
plt.ylabel("RPM")
plt.title("Könnun á svörun viftu")
plt.legend()
plt.savefig('nidurstodur.png')
##Slokkva á viftu
setFanSpeed(PWM_OFF)
GPIO.setup(RELAY_FAN_GPIO_PIN, GPIO.OUT, initial=GPIO.HIGH) # HIGH MEANS RELAY IS OFF
GPIO.cleanup() # resets all GPIO ports used by this function
####
