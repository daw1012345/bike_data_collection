#!/usr/bin/env python3
import base64
import os


def get_mac() -> str:
    # https://stackoverflow.com/questions/159137/getting-mac-address
    try:
        mac = open("/sys/class/net/wlan0/address").readline()
    except:
        mac = "00:00:00:00:00:00"
    return mac[0:17]


def calculate_password(mac: str) -> str:
    # THIS IS NOT SECURE! But it is not meant to be.
    return base64.b64encode(
        bytes(str(int(f"0x{mac.replace(':', '').upper()}", base=0) * 256), "ascii")
    ).decode("ascii")


def apply_config():
    mac = get_mac()
    os.system("nmcli con delete Hotspot")
    os.system(
        f"nmcli dev wifi hotspot ifname wlan0 ssid RPI_BDC_{mac[9:].replace(':', '').upper()} password \"{calculate_password(mac)}\""
    )
    print(calculate_password(mac))


def main():
    apply_config()


if __name__ == "__main__":
    main()
