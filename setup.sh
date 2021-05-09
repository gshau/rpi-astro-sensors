#!/bin/bash
echo Installing python 
apt install python3-pip libatlas-base-dev

echo Installing python libraries
pip3 install -r requirements.txt

echo Registering and enabling service
cp astro-sensor.service /etc/systemd/system
systemctl enable astro-sensor.service
