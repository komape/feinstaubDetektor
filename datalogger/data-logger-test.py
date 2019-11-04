from __future__ import print_function
import serial
import struct
import sys
import time
import json
from datetime import datetime
import Adafruit_DHT

DEBUG = 0
CMD_MODE = 2
CMD_QUERY_DATA = 4
CMD_DEVICE_ID = 5
CMD_SLEEP = 6
CMD_FIRMWARE = 7
CMD_WORKING_PERIOD = 8
MODE_ACTIVE = 0
MODE_QUERY = 1

DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4

ser = serial.Serial()
ser.port = "/dev/ttyUSB0"
ser.baudrate = 9600

ser.open()
ser.flushInput()

byte, data = 0, ""


def dump(d, prefix=''):
    print(prefix + ' '.join(x.encode('hex') for x in d))


def construct_command(cmd, data=[]):
    assert len(data) <= 12
    data += [0, ]*(12-len(data))
    checksum = (sum(data)+cmd-2) % 256
    ret = "\xaa\xb4" + chr(cmd)
    ret += ''.join(chr(x) for x in data)
    ret += "\xff\xff" + chr(checksum) + "\xab"

    if DEBUG:
        dump(ret, '> ')
    return ret


def process_data(d):
    r = struct.unpack('<HHxxBB', d[2:])
    pm25 = r[0]/10.0
    pm10 = r[1]/10.0
    checksum = sum(ord(v) for v in d[2:8]) % 256
    return [pm25, pm10]


def read_response():
    byte = 0
    while byte != "\xaa":
        byte = ser.read(size=1)

    d = ser.read(size=9)

    if DEBUG:
        dump(d, '< ')
    return byte + d


def cmd_set_mode(mode=MODE_QUERY):
    ser.write(construct_command(CMD_MODE, [0x1, mode]))
    read_response()


def cmd_query_data():
    ser.write(construct_command(CMD_QUERY_DATA))
    d = read_response()
    values = []
    if d[1] == "\xc0":
        values = process_data(d)
    return values


def cmd_set_sleep(sleep=1):
    mode = 0 if sleep else 1
    ser.write(construct_command(CMD_SLEEP, [0x1, mode]))
    read_response()


if __name__ == "__main__":
    cmd_set_sleep(0)
    cmd_set_mode(1)
    while True:
        values = cmd_query_data()
        if values is not None:
            print("PM2.5: ", values[0], ", PM10: ", values[1])
        else:
            print("Failed to retrieve data from SDS011")
        humidity, temperature = Adafruit_DHT.read_retry(
            DHT_SENSOR, DHT_PIN)
        if humidity is not None and temperature is not None:
            print("Humidity: {0:0.1f}, Temperature: {1:0.1f}".format(
                humidity, temperature))
        else:
            print("Failed to retrieve data from DHT22")
        time.sleep(2)
