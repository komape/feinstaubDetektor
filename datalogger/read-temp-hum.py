import sys
import time
import Adafruit_DHT

DHT_PIN = 4
DHT_SENSOR = Adafruit_DHT.DHT22

# warm up the sensor
for t in range(14):
    Adafruit_DHT.read_retry(
        DHT_SENSOR, DHT_PIN)
    time.sleep(2)

# read from sensor
humidity, temperature = Adafruit_DHT.read_retry(
    DHT_SENSOR, DHT_PIN)

# check values
if(humidity is None or temperature is None):
    print("ERROR: failed to read from DHT22")

# round values
temperature = round(temperature, 1)
humidity = round(humidity, 1)

# print values
print("temp=" + str(temperature))
print("hum=" + str(humidity))

sys.stdout.flush()