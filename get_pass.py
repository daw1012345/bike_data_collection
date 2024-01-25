#!/usr/bin/env python3
import argparse
import base64

def calculate_password(mac: str) -> str:
    # THIS IS NOT SECURE! But it is not meant to be.
    return base64.b64encode(bytes(str(int(f"0x{mac.replace(':', '').upper()}", base=0)*256), 'ascii')).decode('ascii')

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("--mac", required=True)
	args, _ = parser.parse_known_args()
	print(calculate_password(args.mac))
