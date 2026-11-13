
from dataclasses import dataclass

from someipy import Event, EventGroup, Method, ServiceBuilder, TransportLayerProtocol
from someipy.serialization import SomeIpPayload, Sint16, Uint8


# Service configuration
CLIMATE_SERVICE_ID = 0x2234
CLIMATE_INSTANCE_ID = 0x0001
CLIMATE_MAJOR_VERSION = 1


# Method IDs
GET_CABIN_TEMPERATURE_METHOD_ID = 0x0001
SET_TARGET_TEMPERATURE_METHOD_ID = 0x0002


# Event IDs
CABIN_TEMPERATURE_CHANGED_EVENT_ID = 0x8001
CABIN_TEMPERATURE_EVENTGROUP_ID = 0x0001


# Target temperature limits (tenths of degree Celsius)
MIN_TARGET_TEMPERATURE = 160  # 16.0°C
MAX_TARGET_TEMPERATURE = 300  # 30.0°C


# Response status codes
ACCEPTED = 0
INVALID_TEMPERATURE = 1


@dataclass
class CabinTemperaturePayload(SomeIpPayload):
    temperature: Sint16

    def __init__(self, temperature: int = 240):
        self.temperature = Sint16(temperature)


@dataclass
class TargetTemperaturePayload(SomeIpPayload):
    temperature: Sint16

    def __init__(self, temperature: int = 220):
        self.temperature = Sint16(temperature)


@dataclass
class SetTargetTemperatureResponsePayload(SomeIpPayload):
    status: Uint8

    def __init__(self, status: int = ACCEPTED):
        self.status = Uint8(status)


# Methods
get_cabin_temperature_method = Method(
    id=GET_CABIN_TEMPERATURE_METHOD_ID,
    protocol=TransportLayerProtocol.UDP,
)

set_target_temperature_method = Method(
    id=SET_TARGET_TEMPERATURE_METHOD_ID,
    protocol=TransportLayerProtocol.UDP,
)


# Events
cabin_temperature_changed_event = Event(
    id=CABIN_TEMPERATURE_CHANGED_EVENT_ID,
    protocol=TransportLayerProtocol.UDP,
)

cabin_temperature_eventgroup = EventGroup(
    id=CABIN_TEMPERATURE_EVENTGROUP_ID,
    events=[cabin_temperature_changed_event],
)


# Climate Service definition
climate_service = (
    ServiceBuilder()
    .with_service_id(CLIMATE_SERVICE_ID)
    .with_major_version(CLIMATE_MAJOR_VERSION)
    .with_method(get_cabin_temperature_method)
    .with_method(set_target_temperature_method)
    .with_eventgroup(cabin_temperature_eventgroup)
    .build()
)
