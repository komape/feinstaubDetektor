from __future__ import print_function
import serial
import struct
import sys
import time
import json
import requests
import logging
from logging.handlers import TimedRotatingFileHandler
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

DHT_PIN = 4
DHT_SENSOR = Adafruit_DHT.DHT22

formatter = logging.Formatter(
    "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
handler = TimedRotatingFileHandler(
    "/home/pi/logfile.log", when='midnight', backupCount=10)
handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

ser = serial.Serial()
ser.port = "/dev/ttyUSB0"
ser.baudrate = 9600

ser.open()
ser.flushInput()

byte, data = 0, ""

def dump(d, prefix=''):
    logger.info(prefix + ' '.join(x.encode('hex') for x in d))

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

def do_your_job():
    cmd_set_sleep(0)
    cmd_set_mode(1)
    for t in range(14):
        cmd_query_data()
        Adafruit_DHT.read_retry(
            DHT_SENSOR, DHT_PIN)
        time.sleep(2)
    values = cmd_query_data()
    if values is None:
        logger.error("Failed to retrieve data from SDS011")

    humidity, temperature = Adafruit_DHT.read_retry(
        DHT_SENSOR, DHT_PIN)
    if(humidity is None or temperature is None):
        logger.error("Failed to retrieve data from DHT22")

    logger.info(
        "PM2.5: {0:0.1f}, PM10: {1:0.1f}".format(values[0], values[1]))
    logger.info("Humidity: {0:0.1f}, Temperature: {1:0.1f}".format(
        humidity, temperature))

    # round values
    values[0] = round(values[0], 1)
    values[1] = round(values[1], 1)
    temperature = round(temperature, 1)
    humidity = round(humidity, 1)

    # send data to luftdaten.info and our own database
    push_to_luftdaten(values, humidity, temperature)
    # push_to_database(values, humidity, temperature)

    # print("Going to sleep for 4.5min...")
    cmd_set_mode(0)
    cmd_set_sleep()

def push_to_luftdaten(values, humidity, temperature):
    url = "https://api.sensor.community/v1/push-sensor-data/"
    x_pin_sds011 = '1'
    x_pin_dht22 = '7'
    x_sensor = 'raspi-000000007da5a515'
    headers = {'Content-Type': 'application/json',
               'X-Pin': x_pin_sds011, "X-Sensor": x_sensor}
    data = {"sensordatavalues": [{"value_type": "P1", "value": values[1]}, {
        "value_type": "P2", "value": values[0]}]}

    try:
        r = requests.post(url, headers=headers, data=json.dumps(data))
        if(r.status_code == 201):
            logger.info(r.status_code)
            logger.info(r.json())
        else:
            logger.error('Could not connect to database: Error ' +
                         str(r.status_code) + ': ' + str(r.text))
    except requests.exceptions.RequestException as e:
        logger.error(e)

    headers = {'Content-Type': 'application/json',
               'X-Pin': x_pin_dht22, "X-Sensor": x_sensor}
    data = {"sensordatavalues": [{"value_type": "temperature", "value": temperature}, {
        "value_type": "humidity", "value": humidity}]}

    try:
        r = requests.post(url, headers=headers, data=json.dumps(data))
        if(r.status_code == 201):
            logger.info(r.status_code)
            logger.info(r.json())
        else:
            logger.error('Could not connect to database: Error ' +
                         str(r.status_code) + ': ' + str(r.text))
    except requests.exceptions.RequestException as e:
        logger.error(e)


def push_to_database(values, humidity, temperature):
    url = "http://127.0.0.1:8080/data"
    headers = {'Content-Type': 'application/json'}
    data = {'pm10': values[1], 'pm25': values[0],
            'temp': temperature, 'hum': humidity}

    try:
        r = requests.post(url, headers=headers, data=json.dumps(data))
        if(r.status_code == 201):
            logger.info(r.status_code)
            logger.info(r.json())
        else:
            logger.error('Could not connect to database: Error ' +
                         str(r.status_code) + ': ' + str(r.text))
    except requests.exceptions.RequestException as e:
        logger.error(e)


if __name__ == "__main__":
    while True:
        do_your_job()
        time.sleep(270)
