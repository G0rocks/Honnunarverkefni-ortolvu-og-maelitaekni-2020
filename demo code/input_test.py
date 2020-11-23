def castAsInt(a):
  """
  Function takes in value a and attempts to cast it as int, returns "null" if it fails
  """
  try:
    return int(a)
  except:
    return "null"

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

print("Prófum: ",c)