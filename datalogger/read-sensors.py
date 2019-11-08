import sys
import serial
import struct
import time
import Adafruit_DHT

CMD_MODE = 2
CMD_QUERY_DATA = 4
CMD_SLEEP = 6
MODE_QUERY = 1

DHT_PIN = 4
DHT_SENSOR = Adafruit_DHT.DHT22

ser = serial.Serial()
ser.port = "/dev/ttyUSB0"
ser.baudrate = 9600

ser.open()
ser.flushInput()

def construct_command(cmd, data=[]):
    assert len(data) <= 12
    data += [0, ]*(12-len(data))
    checksum = (sum(data)+cmd-2) % 256
    ret = "\xaa\xb4" + chr(cmd)
    ret += ''.join(chr(x) for x in data)
    ret += "\xff\xff" + chr(checksum) + "\xab"
    return ret

def cmd_set_mode(mode=MODE_QUERY):
    ser.write(construct_command(CMD_MODE, [0x1, mode]))
    read_response()

def cmd_set_sleep(sleep=1):
    mode = 0 if sleep else 1
    ser.write(construct_command(CMD_SLEEP, [0x1, mode]))
    read_response()

def read_response():
    byte = 0
    while byte != "\xaa":
        byte = ser.read(size=1)
    d = ser.read(size=9)
    return byte + d

def cmd_query_data():
    ser.write(construct_command(CMD_QUERY_DATA))
    d = read_response()
    values = []
    if d[1] == "\xc0":
        values = process_data(d)
    return values

def process_data(d):
    r = struct.unpack('<HHxxBB', d[2:])
    pm25 = r[0]/10.0
    pm10 = r[1]/10.0
    checksum = sum(ord(v) for v in d[2:8]) % 256
    return [pm25, pm10]

# wake up sensor
cmd_set_sleep(0)
cmd_set_mode(1)

# warm up sensor
for t in range(14):
    cmd_query_data()
    Adafruit_DHT.read_retry(
        DHT_SENSOR, DHT_PIN)
    time.sleep(2)

# read values
values = cmd_query_data()
if (values is None):
    print("ERROR: failed to read from SDS011")
humidity, temperature = Adafruit_DHT.read_retry(
    DHT_SENSOR, DHT_PIN)
if(humidity is None or temperature is None):
    print("ERROR: failed to read from DHT22")

# round values
values[0] = round(values[0], 1)
values[1] = round(values[1], 1)
temperature = round(temperature, 1)
humidity = round(humidity, 1)

# print values
print("pm10=" + str(values[1]))
print("pm25=" + str(values[0]))
print("temp=" + str(temperature))
print("hum=" + str(humidity))

cmd_set_mode(0)
cmd_set_sleep()

sys.stdout.flush()