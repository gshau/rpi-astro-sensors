import os

import pandas as pd
import json
import time
import numpy as np

import paho.mqtt.client as mqtt
from random import randrange
import time

from multiprocessing import Process

import bme280
from smbus2 import SMBus
from mlx90614 import MLX90614
from flask import Flask, jsonify, request, url_for

import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(module)s %(message)s")
log = logging.getLogger(__name__)


app = Flask(__name__)


BME_ADDRESS = 0x76
MLX_ADDRESS = 0x5A


bus = SMBus(1)
sensor = MLX90614(bus, MLX_ADDRESS)
calibration_params = bme280.load_calibration_params(bus, BME_ADDRESS)


def get_data():
    data = {}
    bme_data = bme280.sample(bus, BME_ADDRESS, calibration_params)
    data["timestamp"] = str(bme_data.timestamp)
    data["temperature"] = bme_data.temperature
    data["pressure"] = bme_data.pressure
    data["humidity"] = bme_data.humidity
    data["ambient_temp"] = sensor.get_ambient()
    data["ir_temp"] = sensor.get_object_1()
    data["temp_diff"] = data["ambient_temp"] - data["ir_temp"]
    return data


def push_data():
    ip_address = "10.0.5.50"
    client = mqtt.Client("astro_sensor", clean_session=False)
    client.connect(ip_address)
    while True:
        log.info("Pushing data")
        data = get_data()
        client.publish("sensors/astro_sensor", json.dumps(data))
        time.sleep(15)


@app.route("/")
def flask_data():
    data = get_data()
    return jsonify(**data)


@app.route("/mqtt/broker/get")
def get_mqtt_broker():
    return jsonify(**{"ip": ip_address})


if __name__ == "__main__":
    p = Process(target=push_data)
    p.start()
    app.run(debug=True, use_reloader=False, host="0.0.0.0", port=9999)
    p.join()
