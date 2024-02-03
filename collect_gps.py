#!/usr/bin/env python3
import gps
import datetime

DATA_PATH = "/home/scb1/gps_data.csv"


def run():
    # This is almost verbatim from https://gpsd.gitlab.io/gpsd/gpsd-client-example-code.html
    session = gps.gps(mode=gps.WATCH_ENABLE)

    try:
        while 0 == session.read():
            if not (gps.MODE_SET & session.valid):
                # not useful, probably not a TPV message
                continue

            if gps.isfinite(session.fix.latitude) and gps.isfinite(
                session.fix.longitude
            ):
                with open(DATA_PATH, "a") as fd:
                    fd.write(
                        f"{datetime.datetime.now().isoformat()},{session.fix.latitude:.6f},{session.fix.longitude:.6f}\n"
                    )
                    fd.flush()
            else:
                print("No useful data")

    except KeyboardInterrupt:
        print("[-] Got interrupted")
    session.close()


if __name__ == "__main__":
    print("[+] Started!")
    run()
    print("[-] Exitting...")
