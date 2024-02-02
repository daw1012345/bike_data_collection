#!/bin/bash
set -e

# Install Deps
apt update
apt install -y nginx python3-websockets python3-bleak

# https://learn.adafruit.com/adding-a-real-time-clock-to-raspberry-pi/set-rtc-time
# HW RTC Clock Setup
raspi-config nonint do_i2c 0
systemctl disable fake-hwclock
apt-get -y remove fake-hwclock
update-rc.d -f fake-hwclock remove

echo "dtoverlay=i2c-rtc,pcf8523" >> /boot/config.txt

timedatectl set-timezone Europe/Amsterdam

# Install Python scripts
mkdir -p /opt/bike_data_collection/
mkdir -p /opt/bike_data_collection/webroot
mkdir -p /opt/collected_data/

cp buttons.py /opt/bike_data_collection/
cp polar_iface.py /opt/bike_data_collection/
cp orchestrator.py /opt/bike_data_collection/
cp wifi_start.py /opt/bike_data_collection/

chmod a+rwx /opt/bike_data_collection/
chmod a+rwx /opt/collected_data/

cp ap-config.service /lib/systemd/system/
cp bike-collect.service /lib/systemd/system/

# Interface setup
cp -r interface/dist/* /opt/bike_data_collection/webroot
cp bike.conf /etc/nginx/sites-available/
ln -s /etc/nginx/sites-available/bike.conf /etc/nginx/sites-enabled/bike.conf 
rm /etc/nginx/sites-enabled/default
systemctl enable --now nginx

systemctl daemon-reload
systemctl enable --now bike-collect
systemctl enable --now ap-config

# Serial Things
# raspi-config nonint do_serial_cons 1
# raspi-config nonint do_serial_hw 0

# GPS Things
# cp gpsd /etc/default/
# systemctl enable --now gpsd

# echo "Reboot to apply everything"