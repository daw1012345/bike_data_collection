import RPi.GPIO as GPIO
import time
from dataclasses import dataclass
from typing import Optional, List
from enum import IntEnum
import datetime

"""Describes an LED State"""


class LEDState(IntEnum):
    ON = 0
    OFF = 1
    LOOP = 2


"""Describes an LED action"""


@dataclass
class LEDActionDescription:
    """The state the LED should be put into"""

    action: LEDState
    """The duration the LED should stay in said state"""
    duration: int


"""Describes a button"""


@dataclass
class ButtonDescription:
    """A name for the button without spaces, special chars."""

    slug: str
    """A human-readable name for the button"""
    name: str
    """A description of the button (unused)"""
    description: str
    """Pin that should be associated to the button"""
    pin: int
    """Debounce period for the button"""
    bounce: int


"""The pin to which the LED is connected"""
GPIO_LED_1 = 8

"""LED light show for after launch"""
LED_ACTION_LAUNCH: List[LEDActionDescription] = [
    LEDActionDescription(action=LEDState.ON, duration=5000),
    LEDActionDescription(action=LEDState.OFF, duration=1),
]

"""LED light show for any success"""
LED_ACTION_SUCCESS: List[LEDActionDescription] = [
    LEDActionDescription(action=LEDState.ON, duration=300),
    LEDActionDescription(action=LEDState.OFF, duration=1),
]

""" Path where collected data is written to"""
DATA_PATH = "/home/scb1/collected_data.csv"

"""A list of configured buttons"""
BUTTONS = [
    ButtonDescription(
        slug="pleasant_1", name="Pleasantness 1", description="", bounce=500, pin=21
    ),
    ButtonDescription(
        slug="pleasant_2", name="Pleasantness 2", description="", bounce=500, pin=24
    ),
    ButtonDescription(
        slug="pleasant_3", name="Pleasantness 2", description="", bounce=500, pin=25
    ),
]

"""
Finds a button description depending on the pin. Useful for 
"""


def get_button(pin: int) -> Optional[ButtonDescription]:
    btn = list(filter(lambda x: x.pin == pin, BUTTONS))
    return btn[0] if btn else None


"""
Executed every time a configured button is pressed. Appends the event to a CSV file immedietally. 
"""


def handle_button_press(channel):
    button = get_button(channel)
    if not button:
        print(f"[-] Unknown button pressed [pin={channel}]")
        return
    print(f"Pressed button [name={button.name}]")

    with open(DATA_PATH, "a") as fd:
        button_entry = f"{datetime.datetime.now().isoformat()},{button.slug}\n"
        fd.write(button_entry)
        fd.flush()

    execute_led_action(LED_ACTION_SUCCESS)


"""
Follows a set of LEDActionDescriptions to create a simple LED effect.
"""


def execute_led_action(action: List[LEDActionDescription]):
    for act in action:
        if act.action == LEDState.ON:
            GPIO.output(GPIO_LED_1, GPIO.HIGH)
        else:
            GPIO.output(GPIO_LED_1, GPIO.LOW)

        time.sleep(act.duration / 1000)


"""
Setup function, should be ran before anything else. Configures all the GPIO pins.
"""


def setup():
    GPIO.setmode(GPIO.BCM)
    for button in BUTTONS:
        GPIO.setup(button.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(
            button.pin,
            GPIO.RISING,
            bouncetime=button.bounce,
            callback=handle_button_press,
        )
    GPIO.setup(GPIO_LED_1, GPIO.OUT)


"""Runs when the file is executed"""
if __name__ == "__main__":
    try:
        setup()
        execute_led_action(LED_ACTION_LAUNCH)
        while True:
            time.sleep(100)
    except:
        GPIO.cleanup()
