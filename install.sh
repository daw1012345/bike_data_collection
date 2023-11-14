#!/bin/bash

# https://learn.adafruit.com/adding-a-real-time-clock-to-raspberry-pi/set-rtc-time
raspi-config nonint do_i2c 0
systemctl disable fake-hwclock
apt-get -y remove fake-hwclock
update-rc.d -f fake-hwclock remove

mv hwclock-set /lib/udev/hwclock-set

echo "dtoverlay=i2c-rtc,pcf8523" >> /boot/config.txt

mkdir -p /opt/data_collection_bike/
cp collect.py /opt/data_collection_bike/
chmod a+rwx /opt/data_collection_bike/
chmod a+x /opt/data_collection_bike/collect.py

cp bike-collect.service /lib/systemd/system/

systemctl daemon-reload
systemctl enable --now bike-collect.service 