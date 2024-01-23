import asyncio
from bleak import BleakClient, BleakScanner
from enum import IntEnum
from dataclasses import dataclass
import signal
from typing import List, Any, Mapping, Set
import json
import sys
import argparse
import datetime
import pytz
from collections import defaultdict

# address = "DF:EF:DB:F6:20:16"
SERVICE = "fb005c80-02e7-f387-1cad-8acd2d8df0c8"
SERVICE_NOTIFY_PORT = "fb005c82-02e7-f387-1cad-8acd2d8df0c8"
SERVICE_CONTROL_PORT = "fb005c81-02e7-f387-1cad-8acd2d8df0c8"

# Something similar: https://github.com/kbre93/dont-hold-your-breath/blob/master/PolarH10.py

@dataclass
class PolarSample:
    time: datetime.datetime
    sample: "PMDFrame"

class PolarContext():
    _sample_queue = asyncio.Queue()

    _print_queue = asyncio.Queue()
    _shutdown_event: asyncio.Event = asyncio.Event()

    _lock: asyncio.Lock = asyncio.Lock()

    def __init__(self, project: str):
        self._project = project
    
    def get_project(self) -> str:
        return self._project

    async def wait_for_sample(self) -> PolarSample:
        return await self._sample_queue.get()

    async def put_sample(self, sample: PolarSample):
        await self._sample_queue.put(sample)

    def did_deal_with_sample(self):
        self._sample_queue.task_done()
    
    async def print_log(self, message: str):
        await self._print_queue.put(json.dumps({"component": "polar", "data": {"log": message}}))
    
    async def print_preformatted(self, message: str):
        await self._print_queue.put(message)

    async def get_next_print(self):
        return await self._print_queue.get()

    def did_print(self):
        self._print_queue.task_done()

    def did_shutdown(self):
        return self._shutdown_event.is_set()

    def shutdown(self):
        self._shutdown_event.set()

    async def wait_for_shutdown(self):
        await self._shutdown_event.wait()


class PMDSetting(IntEnum):
    samplerate = 0
    resolution = 1
    range = 2
    rangeMU = 3
    channels = 4
    factor = 5
    security = 6

class PMDConfiguration:
    # TODO: Implement
    _settings: Mapping[PMDSetting, int] = dict()

    def set():
        pass

    def get() -> int:
        return 0
    
    def clear():
        pass

    def serialize() -> bytes:
        return bytes()

class PMDMeasurmentTypes(IntEnum):
    ECG = 0
    PPG = 1
    ACC = 2
    PPI = 3
    GYRO = 5
    MGN = 6
    SDKMODE = 9
    LOCATION = 10
    PRESSURE = 11
    TEMPERATURE = 12
    OFFLINE_RECORDING = 13
    OFFLINE_HR = 14

class PMDSaveLocation(IntEnum):
    ONLINE = 0
    OFFLINE = 1

    def as_bit_field(self) -> int:
        return self.value << 7
    
class PMDCommands(IntEnum):
    GET_SETTINGS = 0x01
    START_MEASUREMENT = 0x02
    STOP_MEASURMENT = 0x03
    GET_STATUS = 0x05

    # There's more, see https://github.com/polarofficial/polar-ble-sdk/blob/ead9a4077ebc31e745192e0effeebacfd0ec2fa9/sources/iOS/ios-communications/Sources/iOSCommunications/ble/api/model/gatt/client/pmd/PmdControlPointCommand.swift

class PMDError(IntEnum):
    success = 0
    invalid_op = 1
    invalid_measurment = 2
    not_supported = 3
    invalid_len = 4
    invalid_param = 5
    already_in_state = 6
    invalid_resolution = 7
    invalid_sample_rate = 8
    invalud_range = 9
    invalid_mtu = 10
    invalud_num_channels = 11
    invalid_state = 12
    error_charging = 13
    disk_full = 14

@dataclass(frozen=True)
class PMDFrame:
    measurment_type: PMDMeasurmentTypes
    timestamp: int 
    frame_type: int 
    is_compressed: bool
    content: Any

@dataclass(frozen=True)
class PMDCPResponse:
    response: int
    op: int
    measurement: PMDMeasurmentTypes
    error: PMDError
    rest: bytes

@dataclass(frozen=True)
class EcgSample:
    timestamp: int # uint64
    mv: int # int32

@dataclass(frozen=True)
class PMDCECGData:
    timestamp: int
    samples: List[EcgSample]

@dataclass(frozen=True)
class PMDACCData:
    samples: List["PMDACCSample"]

@dataclass(frozen=True)
class PMDACCSample:
    x: int
    y: int
    z: int

def generate_start_message(measurement_type: PMDMeasurmentTypes, location: PMDSaveLocation, settings: PMDConfiguration) -> bytes:
    #  0x00, 0x01, 0x82, 0x00, 0x01, 0x01, 0x0E, 0x00
    base = bytes([PMDCommands.START_MEASUREMENT, location.as_bit_field() | measurement_type])
    if measurement_type == PMDMeasurmentTypes.ECG:
        return base + bytes([0x00, 0x01, 0x82, 0x00, 0x01, 0x01, 0x0E, 0x00])
    else: # For starting ACC measurments
        return base + bytes([0x00, 0x01, 0xC8, 0x00, 0x01, 0x01, 0x10, 0x00, 0x02, 0x01, 0x08, 0x00])
    # return 

def generate_stop_message(measurement_type: PMDMeasurmentTypes, location: PMDSaveLocation) -> bytes:
    return bytes([PMDCommands.STOP_MEASURMENT, location.as_bit_field() | measurement_type])

def parse_pmd_cp_reply(data: bytes) -> Any:
    return PMDCPResponse(
        response=int(data[0]),
        op=data[1],
        measurement=PMDMeasurmentTypes(int(data[2])),
        error=PMDError(int(data[3])),
        rest=data[4:]
    )

def parse_pmd_ecg(data: bytes) -> PMDCECGData | bytes:
    SAMPLE_SIZE = 3
    data_len = len(data)
    if (data_len % SAMPLE_SIZE) != 0 or data_len == 0:
        # print("[-] Malformed ECG packet!")
        return data

    parsed_samples = []
    for i in range(0, data_len, SAMPLE_SIZE):
        parsed_samples.append(EcgSample(timestamp=0, mv=int.from_bytes(data[i:i+SAMPLE_SIZE], byteorder="little", signed=True)))

    return PMDCECGData(timestamp=0, samples=parsed_samples)

def parse_pmd_acc(data: bytes):
    SAMPLE_SIZE = 2
    data_len = len(data)
    if (data_len % (SAMPLE_SIZE*3)) != 0 or data_len == 0:
        # print("Malformed!")
        return data
    
    parsed_samples = []

    for i in range(0, data_len, SAMPLE_SIZE*3):
        parsed_samples.append(PMDACCSample(x=int.from_bytes(data[i:i+SAMPLE_SIZE], byteorder="little", signed=True),y=int.from_bytes(data[i+SAMPLE_SIZE:i+(SAMPLE_SIZE*2)], byteorder="little", signed=True),z=int.from_bytes(data[i+(SAMPLE_SIZE*2):i+(SAMPLE_SIZE*3)], byteorder="little", signed=True)))

    return PMDACCData(parsed_samples)

def parse_pmd_content(data: PMDFrame) -> PMDFrame:
    match data.measurment_type:
        case PMDMeasurmentTypes.ECG:
            return PMDFrame(data.measurment_type, data.timestamp, data.frame_type, data.is_compressed, parse_pmd_ecg(data.content))
        case PMDMeasurmentTypes.ACC:
            return PMDFrame(data.measurment_type, data.timestamp, data.frame_type, data.is_compressed, parse_pmd_acc(data.content))
        case _:
            return data

def parse_pmd_frame(data: bytes) -> PMDFrame | None:
    if len(data) < 11:
        return None

    frame = PMDFrame(
        measurment_type=PMDMeasurmentTypes(int(data[0]) & 0x3F),
        timestamp=int.from_bytes(data[1:9], byteorder="little", signed=False),
        frame_type=int(data[9] & 0x7F),
        is_compressed=(int(data[9]) & 0x80) > 0,
        content=data[10:]
    )

    return parse_pmd_content(frame)


async def pmd_message_handler(ctx: PolarContext, data: bytes):
    frame = parse_pmd_frame(data)
    if not frame:
        await ctx.print_log("Invalid frame!")
        return
    await ctx.put_sample(PolarSample(time=datetime.datetime.now(tz=pytz.utc), sample=frame))


async def pmd_control_handler(_, data: bytes):
    parse_pmd_cp_reply(data)

async def stdout_writer(ctx: PolarContext):
    while True:
        if msg := await ctx.get_next_print():
            sys.stdout.write(msg + '\n')
            sys.stdout.flush()
        ctx.did_print()

def sample_writer_fmt(message: PolarSample) -> str:
    formatted_str = ""
    match message.sample.measurment_type:
        case PMDMeasurmentTypes.ECG:
            for sample in message.sample.content.samples:
                formatted_str += f"{message.time.isoformat()},{message.sample.timestamp},{sample.mv}\n"
        case PMDMeasurmentTypes.ACC:
            for sample in message.sample.content.samples:
                formatted_str += f"{message.time.isoformat()},{message.sample.timestamp},{sample.x},{sample.y},{sample.z}\n"

    return formatted_str

async def sample_writer_caller(ctx: PolarContext, message: PolarSample):
    match message.sample.measurment_type:
        case PMDMeasurmentTypes.ECG:
            await ctx.print_preformatted(json.dumps({"component": "polar", "data": {"ecg": f"{message.sample.content.samples[0].mv} mV"}}))
        case PMDMeasurmentTypes.ACC:
            await ctx.print_preformatted(json.dumps({"component": "polar", "data": {"acc": f"{message.sample.content.samples[0].x} mG | {message.sample.content.samples[0].y} mG | {message.sample.content.samples[0].z} mG"}}))

async def sample_writer(ctx: PolarContext):
    SAMPLE_FREQ = 10
    elapsed_per_feature: Mapping[PMDMeasurmentTypes, int] = defaultdict(int)
    fd_per_feature: Mapping[PMDMeasurmentTypes, Any] = defaultdict(lambda: int(SAMPLE_FREQ))

    try:
        for name, value in [("ecg", PMDMeasurmentTypes.ECG), ("acc", PMDMeasurmentTypes.ACC)]:
            fd_per_feature[value] = open(f"{ctx.get_project()}{name}.csv", 'w')

        while True:
            if msg := await ctx.wait_for_sample():
                fd_per_feature[msg.sample.measurment_type].write(sample_writer_fmt(msg))
                elapsed_per_feature[msg.sample.measurment_type] += 1
                if elapsed_per_feature[msg.sample.measurment_type] >= SAMPLE_FREQ:
                    await sample_writer_caller(ctx, msg)
                    elapsed_per_feature[msg.sample.measurment_type] = 0
            ctx.did_deal_with_sample()

    finally:
        for v in fd_per_feature.values():
            v.flush()
            v.close()

async def main(address, project):
    ctx = PolarContext(project)
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, ctx.shutdown)

    write_task = asyncio.create_task(stdout_writer(ctx))
    sample_task = asyncio.create_task(sample_writer(ctx))
    await ctx.print_log(f"Connecting to {address}")

    async def pmd_message_handler_wrapper(_, data: bytes):
        return await pmd_message_handler(ctx, data)

    running = True
    while running and not ctx.did_shutdown():
        try:
            device = await BleakScanner.find_device_by_address(address)
            async with BleakClient(device) as client:
                await ctx.print_log("[+] Connected!")
                # This will automatically stop on disconnect
                await client.start_notify(SERVICE_NOTIFY_PORT, pmd_message_handler_wrapper)
                await client.start_notify(SERVICE_CONTROL_PORT, pmd_control_handler)

                await client.write_gatt_char(SERVICE_CONTROL_PORT,  generate_start_message(PMDMeasurmentTypes.ECG, PMDSaveLocation.ONLINE, None), response=True)
                await client.write_gatt_char(SERVICE_CONTROL_PORT,  generate_start_message(PMDMeasurmentTypes.ACC, PMDSaveLocation.ONLINE, None), response=True)

                await ctx.wait_for_shutdown()

                await ctx.print_log("[+] Shutting down...")
                running = False
                await client.write_gatt_char(SERVICE_CONTROL_PORT,  generate_stop_message(PMDMeasurmentTypes.ECG, PMDSaveLocation.ONLINE), response=True)
                await client.write_gatt_char(SERVICE_CONTROL_PORT,  generate_stop_message(PMDMeasurmentTypes.ACC, PMDSaveLocation.ONLINE), response=True)
                await client.stop_notify(SERVICE_NOTIFY_PORT)
                await client.stop_notify(SERVICE_CONTROL_PORT)

                await write_task.cancel()
                await sample_task.cancel()
                # Disconnect will happen automatically after exit from the with block
        except Exception as e:
            await ctx.print_log(repr(e))
            await ctx.print_log("[-] Connection failed, retrying...")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mac", required=True)
    parser.add_argument("--project", required=True)
    args, _ = parser.parse_known_args()

    asyncio.run(main(args.mac, args.project))