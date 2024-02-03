import RPi.GPIO as GPIO
import time
from dataclasses import dataclass
from typing import Optional, List
from enum import IntEnum
import datetime
import asyncio
import json
import argparse
import signal
import sys
import pytz


class LEDState(IntEnum):
    """Describes an LED State"""

    ON = 0
    OFF = 1
    LOOP = 2


class ButtonContext:
    _shutdown_event = asyncio.Event()
    _print_queue = asyncio.Queue()

    _button_press_queue = asyncio.Queue()

    def __init__(self, project, loop):
        self._project = project
        self._loop = loop

    def get_loop(self):
        return self._loop

    def get_project(self) -> str:
        return self._project

    async def submit_print(self, msg: str):
        await self._print_queue.put(
            json.dumps({"component": "buttons", "data": {"log": msg}})
        )

    async def submit_print_preformatted(self, msg: str):
        await self._print_queue.put(msg)

    async def wait_for_print(self) -> str:
        return await self._print_queue.get()

    def print_done(self):
        self._print_queue.task_done()

    async def submit_button_press(self, button: "ButtonDescription"):
        await self._button_press_queue.put(button)

    async def wait_for_button_press(self) -> "ButtonDescription":
        return await self._button_press_queue.get()

    def button_press_done(self):
        self._button_press_queue.task_done()

    async def wait_for_shutdown(self):
        await self._shutdown_event.wait()

    def shutdown(self):
        self._shutdown_event.set()


@dataclass
class LEDActionDescription:
    """Describes an LED action"""

    """The state the LED should be put into"""
    action: LEDState
    """The duration the LED should stay in said state"""
    duration: int


"""Describes a button"""


@dataclass
class ButtonDescription:
    """Describes an LED action"""

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
GPIO_LED_1 = 19

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

"""A list of configured buttons"""
BUTTONS = [
    ButtonDescription(
        slug="pleasant_1", name="Pleasantness 1", description="", bounce=500, pin=21
    ),
    ButtonDescription(
        slug="pleasant_2", name="Pleasantness 2", description="", bounce=500, pin=16
    ),
    ButtonDescription(
        slug="pleasant_3", name="Pleasantness 2", description="", bounce=500, pin=20
    ),
]


def get_button(pin: int) -> Optional[ButtonDescription]:
    """
    Finds a button description depending on the pin.
    """
    btn = list(filter(lambda x: x.pin == pin, BUTTONS))
    return btn[0] if btn else None


async def print_handler(ctx: ButtonContext):
    while True:
        if msg := await ctx.wait_for_print():
            sys.stdout.write(f"{msg}\n")
            sys.stdout.flush()
        ctx.print_done()


async def write_handler(ctx: ButtonContext):
    with open(f"{ctx.get_project()}buttons.csv", "w") as fd:
        while True:
            if button := await ctx.wait_for_button_press():
                await ctx.submit_print_preformatted(
                    json.dumps(
                        {"component": "buttons", "data": {"button": button.slug}}
                    )
                )
                button_entry = (
                    f"{datetime.datetime.now(tz=pytz.utc).isoformat()},{button.slug}\n"
                )
                fd.write(button_entry)
                fd.flush()
            ctx.button_press_done()


def handle_button_press(ctx: ButtonContext, channel):
    """
    Executed every time a configured button is pressed. Appends the event to a CSV file immedietally.
    """
    button = get_button(channel)
    if not button:
        return

    async def press_wrapper():
        await ctx.submit_button_press(button)

    asyncio.run_coroutine_threadsafe(press_wrapper(), ctx.get_loop())

    execute_led_action(LED_ACTION_SUCCESS)


def execute_led_action(action: List[LEDActionDescription]):
    """
    Follows a set of LEDActionDescriptions to create a simple LED effect.
    """
    for act in action:
        if act.action == LEDState.ON:
            GPIO.output(GPIO_LED_1, GPIO.HIGH)
        else:
            GPIO.output(GPIO_LED_1, GPIO.LOW)

        time.sleep(act.duration / 1000)


def setup(ctx):
    """
    Setup function, should be ran before anything else. Configures all the GPIO pins.
    """

    def press_wrapper(channel):
        handle_button_press(ctx, channel)

    GPIO.setwarnings(False)

    GPIO.setmode(GPIO.BCM)
    for button in BUTTONS:
        GPIO.setup(button.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(
            button.pin,
            GPIO.RISING,
            bouncetime=button.bounce,
            callback=press_wrapper,
        )
    GPIO.setup(GPIO_LED_1, GPIO.OUT)


async def main(project):
    ctx = ButtonContext(project, asyncio.get_event_loop())
    ctx.get_loop().add_signal_handler(signal.SIGINT, ctx.shutdown)
    ctx.get_loop().add_signal_handler(signal.SIGTERM, ctx.shutdown)
    print_task = asyncio.create_task(print_handler(ctx))
    write_task = asyncio.create_task(write_handler(ctx))

    try:
        setup(ctx)
        execute_led_action(LED_ACTION_LAUNCH)
        await ctx.wait_for_shutdown()
    finally:
        print_task.cancel()
        write_task.cancel()
        GPIO.cleanup()


"""Runs when the file is executed"""
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    args, _ = parser.parse_known_args()
    asyncio.run(main(args.project))
