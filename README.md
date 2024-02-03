# Bike Data Collection Suite
This project collects data from a Polar H10 device and a of buttons. It's controllable via an interface.
## Installation
```bash
# sudo ./install.sh
# sudo reboot
```
## Use
- After rebooting, the RPi will start a Wi-Fi network with the prefix `RPI_BDC_`. The `wifi_to_pass.py` script can be used to get the password for the network. This is not secure, but it wasn't intended to be. This can always be adjusted.
- To begin data collection, connect to the Wi-Fi network and navigate to `http://10.42.0.1`.
- To adjust/add buttons, edit `buttons.py` located in `/opt/bike_data_collection/` on the RPi, or simply edit the file locally and re-install.

