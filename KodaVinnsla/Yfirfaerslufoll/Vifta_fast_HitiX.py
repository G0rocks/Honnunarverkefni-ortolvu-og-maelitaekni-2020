import RPi.GPIO as GPIO
import time
import board
import adafruit_dht
import datetime
import numpy as np
# import matplotlib.pyplot as plt
# import xlsxwriter


#----------- Configuration -----------#
FAN_GPIO_PIN = 20       # BCM pin used to drive PWM fan
PWM_FREQ = 25000        # [Hz] 25kHz for PWM control

PWM_OFF = 0             # the PWM_duty_cycle 0%
PWM_MAX = 100           # the PWM_duty_cycle 100%

RELAY_FAN_GPIO_PIN = 26 # BCM pin used to turn RELAY for FAN ON/OFF
RELAY_HEATER_FAN_GPIO_PIN = 16 # BCM pin used to turn RELAY for HEATER ON/OFF

dhtDevice = adafruit_dht.DHT22(board.D5) #Hitanemi
upphafshitastig = dhtDevice.temperature # Upphafshitastig
deltaT = 0 # breyta til að fylgjast með breyting á hitastigi

#----------- define functions -----------#
# Stilla viftuhraða
def setFanSpeed(PWM_duty_cycle):
  fan.start(PWM_duty_cycle)    # set the speed according to the PWM duty cycle
  return()

#----------- Inntak á gildum ------------#
# Inntak á gildum 
print("____Yfirfærslufall profun____")
a = int(input("Kveikt á hitara? yes[1],no[2]?: "))
b = int(input("Hvaða duty cycle viltu profa?: "))
print("Ath 1 lota er 5 sek þ.e. 12 lotur mæla í 60 sek")
c = int(input("Hversu margar lotur viltu profa?: "))

#--------------------------------------------#
try:
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    # PWM notað til að stýra viftuhraða
    GPIO.setup(FAN_GPIO_PIN, GPIO.OUT, initial=GPIO.LOW)
    fan = GPIO.PWM(FAN_GPIO_PIN,PWM_FREQ)
    setFanSpeed(PWM_OFF)
    # Setting up relay for HEATER
    GPIO.setup(RELAY_HEATER_FAN_GPIO_PIN, GPIO.OUT, initial=GPIO.HIGH) # HIGH MEANS RELAY IS OFF
    # Setting up relay for FAN
    GPIO.setup(RELAY_FAN_GPIO_PIN, GPIO.OUT, initial=GPIO.LOW) # HIGH MEANS RELAY IS OFF
    
    if(a == 1):
      GPIO.output(RELAY_HEATER_FAN_GPIO_PIN,GPIO.LOW) # Turn the HEATER ON

    

    counter= 0

    #-- Tóm fylki til að vista gögn --#
    arr = np.empty((0,2), int)
    # Cycle_duty = []
    # Hiti = []
    # Timi = []
  
    #-------- Prófun á föstu duty cycle ---------#
    # Prófað er á 5 sek fresti
    startTime = time.time() #Stilla upphafstima
    while (counter < c):
        setFanSpeed(b) # viftuhraði settur í gildi sem var slegið inn í upphafi
        try:
            hitastig = dhtDevice.temperature
            rakastig = dhtDevice.humidity
            deltaT = hitastig - upphafshitastig
            nowTime = time.time()
            Time = nowTime-startTime
            print("Hitastig: {:.1f} C   Timi: {}".format(hitastig,(Time)))
        except RuntimeError as error:
            # Villur koma reglulega upp - getur verið erfitt að lesa gildi nemans, bara reyna aftur
            print(error.args[0])
            time.sleep(2.0)
            continue
        except Exception as error:
            dhtDevice.exit()
            raise error
        arr = np.append(arr, np.array([[Time,hitastig]]), axis=0)
        # Hiti.append(hitastig)
        # Timi.append(nowTime-startTime)
        time.sleep(5)
        counter += 1
    # print(Timi)
    # print(Hiti)
    # ########arr2D = np.array(Timi,Hiti)
# Save 2D numpy array to csv file
    np.savetxt('nidurstodur.csv', arr, delimiter=',', fmt='%d')
# #----------- Afritum gildi í .xlsx file til að geta unnið með þau -----------#
# workbook = xlsxwriter.Workbook('Nidurst.xlsx')
# worksheet = workbook.add_worksheet('Mæling XXX')
# bold = workbook.add_format({'bold': True})
# worksheet.write(0, 0, 'Timi', bold)
# worksheet.write(0, 1, 'Hiti', bold)
# # Byrjum nú í A2
# row = 1
# col = 0
# for i in Timi:
#   worksheet.write(row, col, Timi[i])
#   worksheet.write(row, col + 1, Hiti[i])
#   row += 1

# workbook.close()


  # trap a CTRL+C keyboard interrupt
except KeyboardInterrupt:
    setFanSpeed(PWM_OFF)
    GPIO.cleanup() # resets all GPIO ports used by this function

  #---- Gerum graf fyrir Tima og Hita---#
 
  # graf1 = plt.plot(Timi,Hiti,label= "Hiti sem fall af tíma")
  #   plt.xlabel("Timi [s]")
  #   plt.ylabel("Hiti [C]")
  #   plt.title("Hiti sem fall af Tima")
  #   plt.legend()
  #   plt.savefig('nidurstodur.png')
  

#----------- Núllstilla viftu og hitara í lok keyrslu -----------#
setFanSpeed(0) #slokkva á viftu
GPIO.setup(RELAY_FAN_GPIO_PIN, GPIO.OUT, initial=GPIO.HIGH) # HIGH MEANS RELAY IS OFF
#GPIO.cleanup() # resets all GPIO ports used by this function
