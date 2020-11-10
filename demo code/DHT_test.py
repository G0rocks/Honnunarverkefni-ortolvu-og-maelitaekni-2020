
import time
import board
import adafruit_dht

dhtDevice = adafruit_dht.DHT22(board.D5)

teljari = 1
upphafshitastig = dhtDevice.temperature # Upphafshitastig
deltaT = 0 # breyta til að fylgjast með breyting á hitastigi

while (teljari < 11):
    try:
        hitastig = dhtDevice.temperature
        rakastig = dhtDevice.humidity
        deltaT = hitastig - upphafshitastig
        print(
            "Hitastig: {:.1f} C    Rakastig: {}%  -- deltaT {:.1f}  mæling nr. {}".format(
                hitastig , rakastig, deltaT, teljari
            )
        )

    except RuntimeError as error:
        # Villur koma reglulega upp - getur verið erfitt að lesa gildi nemans, bara reyna aftur
        print(error.args[0])
        time.sleep(2.0)
        continue
    except Exception as error:
        dhtDevice.exit()
        raise error

    time.sleep(2.0)
    teljari = teljari + 1