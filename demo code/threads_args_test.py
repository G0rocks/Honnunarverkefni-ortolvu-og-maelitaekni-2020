from threading import Thread, Event
from time import sleep

event = Event()

def modify_variable(var):
    while True:
        for i in range(len(var)):
            var[i] += 1
        if event.is_set():
            break
        sleep(.5)
    print('Stop printing')

def print_variable(var):
  """
  docstring
  """
  while True:
    print(var)
    sleep(0.5)
    if event.is_set():
      break
  print('Stop thread 2')

my_var = [1, 2, 3]
t = Thread(target=modify_variable, args=(my_var, ))
t2 = Thread(target=print_variable, args=(my_var, ))
t.start()
t2.start()
while True:
    try:
       # print(my_var)
        sleep(2)
    except KeyboardInterrupt:
        event.set()
        break
t.join()
print(my_var)