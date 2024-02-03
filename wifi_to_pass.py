#!/usr/bin/env python3
import argparse
import base64
import sys
import itertools

RPI_MAC_OUI = "D8:3A:DD"
WIFI_PREFIX = "RPI_BDC_"


def calculate_password(mac: str) -> str:
    # THIS IS NOT SECURE! But it is not meant to be.
    return base64.b64encode(
        bytes(str(int(f"0x{mac.replace(':', '').upper()}", base=0) * 256), "ascii")
    ).decode("ascii")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ssid", required=True)
    args = parser.parse_args()

    prefix_len = len(WIFI_PREFIX)
    if not args.ssid.startswith(WIFI_PREFIX) or len(args.ssid) - prefix_len != 6:
        print("Invalid wifi name!")
        sys.exit(-1)

    mac_rhs = ":".join(
        list(map("".join, itertools.batched(args.ssid[prefix_len:], n=2)))
    )
    mac = f"{RPI_MAC_OUI}:{mac_rhs}".upper()

    print(f"Assuming MAC: {mac}")

    print(calculate_password(mac))
