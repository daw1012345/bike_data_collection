#!/bin/bash
set -e

# https://learn.adafruit.com/adding-a-real-time-clock-to-raspberry-pi/set-rtc-time
# HW RTC Clock Setup
raspi-config nonint do_i2c 0
systemctl disable fake-hwclock
apt-get -y remove fake-hwclock
update-rc.d -f fake-hwclock remove

cp hwclock-set /lib/udev/hwclock-set

echo "dtoverlay=i2c-rtc,pcf8523" >> /boot/config.txt

# Install Python scripts
mkdir -p /opt/bike_data_collection/
mkdir -p /opt/bike_data_collection/webroot
mkdir -p /opt/collected_data/

cp buttons.py /opt/bike_data_collection/
cp polar_iface.py /opt/bike_data_collection/
cp orchestrator.py /opt/bike_data_collection/

chmod a+rwx /opt/bike_data_collection/
chmod a+rwx /opt/collected_data/

cp bike-collect.service /lib/systemd/system/
systemctl daemon-reload
systemctl enable --now bike-collect.serivce

# Interface setup
apt install nginx
cp -r interface/dist/* /opt/bike_data_collection/webroot
cp bike.conf /etc/nginx/sites-available/
ln -s /etc/nginx/sites-available/bike.conf /etc/nginx/sites-enabled/bike.conf 
systemctl enable --now nginx

# Serial Things
raspi-config noint do_serial 1 0

# GPS Things
apt update
apt install gpsd gpsd-clients

cp gpsd /etc/default/
systemctl enable --now gpsd

echo "Reboot to apply everything"