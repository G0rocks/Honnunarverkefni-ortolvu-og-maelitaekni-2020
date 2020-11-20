# Testing the threading functionality of the threading module
import threading
from threading import Thread
from time import sleep

def sum(a: int, b: int):
  return (a+b)

def doThing1():
  """
  Does the first thing
  """
  sleep(3)
  print("Thread 1. The sum of 2 and 5 is {int}", sum(2,5))

def doThing2():
  """
  Does the second thing
  """
  print("Thread 2. The sum of 3 and 6 is {int}", sum(2,5))

t1 = threading.Thread(target=doThing1)
t2 = threading.Thread(target=doThing2)

t1.start()
t2.start()
sleep(2)
print("Hey")
