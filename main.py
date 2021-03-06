import time
import logging

import json
import numpy as np

import paho.mqtt.client as mqtt

from multiprocessing import Process

import bme280
from smbus2 import SMBus
from mlx90614 import MLX90614
from flask import Flask, jsonify
from sqm_le import SQM

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(module)s %(message)s"
)  # noqa
log = logging.getLogger(__file__)

app = Flask(__name__)

BME_ADDRESS = 0x76
MLX_ADDRESS = 0x5A

mqtt_broker_address = "10.0.5.50"
sqm_address = "10.0.5.98"
sqm = SQM(ip_address=sqm_address)

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
    if sqm.found_device:
        try:
            sqm_reading = sqm.get_reading()
            data["sqm"] = sqm_reading
        except Exception:
            data["sqm"] = np.nan
    return data


def push_data():
    while True:
        client = mqtt.Client("astro_sensor", clean_session=True)
        client.connect(mqtt_broker_address)
        log.info("Pushing data")
        data = get_data()
        client.publish("sensors/astro_sensor", json.dumps(data))
        client.disconnect()
        time.sleep(15)


@app.route("/sqm/find_ip")
def find_sqm_ip():
    sqm.find_device()
    return str(sqm)


@app.route("/sqm/set_ip/<ip_address>")
def set_sqm_ip(ip_address):
    sqm.ip_address = ip_address
    sqm.found_device = True
    return str(sqm)


@app.route("/")
def flask_data():
    data = get_data()
    return jsonify(**data)


@app.route("/mqtt/broker/get")
def get_mqtt_broker():
    return jsonify(**{"ip": mqtt_broker_address})


if __name__ == "__main__":
    p = Process(target=push_data)
    p.start()
    app.run(debug=True, use_reloader=True, host="0.0.0.0", port=5000)
    p.join()
