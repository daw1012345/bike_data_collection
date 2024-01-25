#!/usr/bin/env python3

# This part of the project is what the React interface will communicate with.
# It starts data collection components
# Possible MSGs:
# {"command": "set_settings", "config": {...}}
# {"command": "get_settings"}
# {"command": "set_enabled_collectors", "collectors": [...]}
# {"command": "get_enabled_collectors"}
# {"command": "start"}
# {"command": "stop"}
# Possible reply:
# {"command": "...", "result": true | false, "message": ""}

import asyncio
from websockets.server import serve
import signal
from typing import Mapping, Set, Collection, List
import json
from dataclasses import dataclass
import pathlib
import os

if os.getenv("BIKE_DEBUG"):
    INSTALL_PATH = "/home/dawid/Documents/Workspace/bike_data_collection/"
else:
    INSTALL_PATH = "/opt/bike_data_collection/"

# Global config
PORT = 9999
HOSTNAME = "0.0.0.0"
if os.getenv("BIKE_DEBUG"):
    BASE_PROJECT_PATH = "/tmp/"
else:
    BASE_PROJECT_PATH = "/opt/collected_data/"


@dataclass(frozen=True)
class CollectorDef:
    name: str
    slug: str
    description: str
    path: str


ALL_AVAILABLE_COLLECTORS: List[CollectorDef] = [
    CollectorDef(
        "polar",
        "polar",
        "The Polar H10 HR and ACC tracking module",
        f"{INSTALL_PATH}polar_iface.py",
    ),
    CollectorDef(
        "Buttons",
        "buttons",
        "Button-based emotion tracking module",
        f"{INSTALL_PATH}buttons.py",
    ),
]


class Configuration:
    _settings: Mapping[str, str] = {}
    _collectors: Set[str] = set()

    def set_collectors(self, collectors: Collection[str]):
        self._collectors = set(collectors)

    def get_collectors(self) -> Set[str]:
        return list(self._collectors)

    def get_settings(self):
        return dict(self._settings)

    def apply_settings(self, new_settings: Mapping[str, str]):
        for key, val in new_settings.items():
            self._settings[key] = val

    def get_as_params(self) -> List[str]:
        params = []
        for k, v in self._settings.items():
            params.append(f"--{k}={v}")
        return params


class OrchestratorContext:
    _shutdown_event = asyncio.Event()
    _connections_lock: asyncio.Lock = asyncio.Lock()
    _connections: Set[any] = set()

    _tasks_lock = asyncio.Lock()
    _tasks = set()

    settings: Configuration = Configuration()

    async def start(self, project: str):
        async with self._tasks_lock:
            for possible_collector in ALL_AVAILABLE_COLLECTORS:
                if possible_collector.slug in self.settings.get_collectors():
                    settings_str = (
                        self.settings.get_as_params()
                        + [f"--project={BASE_PROJECT_PATH}{project}/"]
                    )
                    self._tasks.add(
                        asyncio.create_task(
                            process_handler(possible_collector, settings_str, self)
                        )
                    )

    async def stop(self):
        async with self._tasks_lock:
            for task in self._tasks:
                task.cancel()

            self._tasks.clear()

    async def is_running(self):
        async with self._tasks_lock:
            return bool(self._tasks)

    async def wait_for_shutdown(self):
        await self._shutdown_event.wait()

    def shutdown(self):
        self._shutdown_event.set()

    async def on_connect(self, conn):
        async with self._connections_lock:
            self._connections.add(conn)

    async def on_disconnect(self, conn):
        async with self._connections_lock:
            self._connections.remove(conn)

    async def forward(self, msg: str):
        async with self._connections_lock:
            for conn in self._connections:
                await conn.send(msg)


async def process_handler(
    collector: CollectorDef, params: str, ctx: OrchestratorContext
):
    print(f"Starting: {collector.path} {params}")

    proc = await asyncio.create_subprocess_exec("/usr/bin/python3",
        collector.path, *params, stdout=asyncio.subprocess.PIPE
    )

    try:
        while data := await proc.stdout.readline():
            line = data.decode("ascii").rstrip()
            if line:
                await ctx.forward(line)
    except asyncio.CancelledError:
        proc.terminate()
        raise


async def stop_handler(ctx, msg):
    await ctx.stop()
    return json.dumps({"command": "stop", "result": True, "message": None})


async def start_handler(ctx, msg):
    if await ctx.is_running():
        return json.dumps(
            {"command": "start", "result": False, "message": "Already running!"}
        )

    if "project" not in msg or not msg["project"]:
        return json.dumps(
            {"command": "start", "result": False, "message": "Missing project name!"}
        )

    project = msg["project"]
    project_path = pathlib.Path(f"{BASE_PROJECT_PATH}{project}")

    if project_path.exists():
        return json.dumps(
            {"command": "start", "result": False, "message": "Project already exists!"}
        )

    os.mkdir(str(project_path))

    await ctx.start(project)
    return json.dumps({"command": "start", "result": True, "message": None})


async def set_settings_handler(ctx, msg):
    if await ctx.is_running():
        return json.dumps(
            {
                "command": "set_settings",
                "result": False,
                "message": "Cannot set settings while collectors are running!",
            }
        )

    if "config" not in msg:
        return json.dumps(
            {"command": "set_settings", "result": False, "message": "Corrupted message"}
        )

    if not isinstance(msg["config"], dict):
        return json.dumps(
            {"command": "set_settings", "result": False, "message": "Corrupted message"}
        )

    ctx.settings.apply_settings(msg["config"])

    return json.dumps({"command": "set_settings", "result": True, "message": None})


async def get_settings_handler(ctx, msg):
    return json.dumps(
        {
            "command": "get_settings",
            "result": True,
            "message": ctx.settings.get_settings(),
        }
    )


async def set_collectors_handler(ctx, msg):
    if await ctx.is_running():
        return json.dumps(
            {
                "command": "set_collectors",
                "result": False,
                "message": "Cannot set collectors while running an experiment!",
            }
        )

    if "collectors" not in msg:
        return json.dumps(
            {
                "command": "set_collectors",
                "result": False,
                "message": "Corrupted message",
            }
        )

    if not isinstance(msg["collectors"], list):
        return json.dumps(
            {
                "command": "set_collectors",
                "result": False,
                "message": "Corrupted message",
            }
        )

    ctx.settings.set_collectors(msg["collectors"])
    return json.dumps({"command": "set_collectors", "result": True, "message": None})


async def get_collectors_handler(ctx, msg):
    return json.dumps(
        {
            "command": "get_collectors",
            "result": True,
            "message": ctx.settings.get_collectors(),
        }
    )


async def get_state_handler(ctx, msg):
    return json.dumps(
        {
            "command": "get_state",
            "result": True,
            "message": {
                "collectors": ctx.settings.get_collectors(),
                "is_running": await ctx.is_running(),
            },
        }
    )


async def comms_handler(ctx, msg):
    return "{}"


async def message_handler(ctx: OrchestratorContext, websocket):
    HANDLERS = {
        "get_state": get_state_handler,
        "stop": stop_handler,
        "start": start_handler,
        "set_settings": set_settings_handler,
        "get_settings": get_settings_handler,
        "set_collectors": set_collectors_handler,
        "get_collectors": get_collectors_handler,
        "comms": comms_handler,
    }

    await ctx.on_connect(websocket)

    async for message in websocket:
        print(message)
        try:
            message: dict = json.loads(message)
        except json.decoder.JSONDecodeError:
            await websocket.send(
                json.dumps(
                    {
                        "command": "unknown",
                        "result": False,
                        "message": "Malformed command!",
                    }
                )
            )
            continue

        if "command" not in message:
            await websocket.send(
                json.dumps(
                    {
                        "command": "unknown",
                        "result": False,
                        "message": "Malformed command!",
                    }
                )
            )
            continue

        if message["command"] in HANDLERS:
            await websocket.send(await HANDLERS[message["command"]](ctx, message))
        else:
            await websocket.send(
                json.dumps(
                    {
                        "command": message["command"],
                        "result": False,
                        "message": "Malformed command!",
                    }
                )
            )

    await ctx.on_disconnect(websocket)


async def main():
    ctx = OrchestratorContext()
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, ctx.shutdown)

    async def handler_wrapper(websocket):
        await message_handler(ctx, websocket)

    async with serve(handler_wrapper, HOSTNAME, PORT):
        await ctx.wait_for_shutdown()


if __name__ == "__main__":
    asyncio.run(main())
