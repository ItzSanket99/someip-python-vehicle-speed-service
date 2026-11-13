
"""
Climate ECU - SOME/IP Service Provider.

Provides:
1. GetCabinTemperature method
2. SetTargetTemperature method
3. CabinTemperatureChanged event
"""

import asyncio
import logging

from someipy import (
    MessageType,
    Method,
    MethodResult,
    ReturnCode,
    ServerServiceInstance,
    ServiceBuilder,
    TransportLayerProtocol,
    connect_to_someipy_daemon,
)

from someipy.someipy_logging import set_someipy_log_level

from climate_interface import (
    CLIMATE_SERVICE_ID,
    CLIMATE_INSTANCE_ID,
    CLIMATE_MAJOR_VERSION,
    GET_CABIN_TEMPERATURE_METHOD_ID,
    SET_TARGET_TEMPERATURE_METHOD_ID,
    CABIN_TEMPERATURE_CHANGED_EVENT_ID,
    CABIN_TEMPERATURE_EVENTGROUP_ID,
    MIN_TARGET_TEMPERATURE,
    MAX_TARGET_TEMPERATURE,
    ACCEPTED,
    INVALID_TEMPERATURE,
    CabinTemperaturePayload,
    TargetTemperaturePayload,
    SetTargetTemperatureResponsePayload,
    cabin_temperature_eventgroup,
)


# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Climate state
# ------------------------------------------------------------------

current_cabin_temperature = 240  # 24.0°C
target_temperature = 220         # 22.0°C


# ------------------------------------------------------------------
# Helper: Create SOME/IP method response
# ------------------------------------------------------------------

def create_method_response(payload):

    result = MethodResult()
    result.message_type = MessageType.RESPONSE
    result.return_code = ReturnCode.E_OK
    result.payload = payload

    return result


# ------------------------------------------------------------------
# GetCabinTemperature method handler
# ------------------------------------------------------------------

async def get_cabin_temperature_handler(input_data, client_address):

    logger.info(
        "GetCabinTemperature request received from %s",
        client_address,
    )

    logger.info(
        "Current cabin temperature: %.1f°C",
        current_cabin_temperature / 10,
    )

    payload = CabinTemperaturePayload(
        current_cabin_temperature
    ).serialize()

    return create_method_response(payload)


# ------------------------------------------------------------------
# SetTargetTemperature method handler
# ------------------------------------------------------------------

async def set_target_temperature_handler(input_data, client_address):

    global target_temperature

    logger.info(
        "SetTargetTemperature request received from %s",
        client_address,
    )

    request_payload = TargetTemperaturePayload().deserialize(input_data)
    requested_temperature = int(request_payload.temperature.value)

    requested_temperature = int(requested_temperature)

    logger.info(
        "Requested target temperature: %.1f°C",
        requested_temperature / 10,
    )

    if (
        MIN_TARGET_TEMPERATURE
        <= requested_temperature
        <= MAX_TARGET_TEMPERATURE
    ):

        target_temperature = requested_temperature
        status = ACCEPTED

        logger.info(
            "Target temperature updated to %.1f°C",
            target_temperature / 10,
        )

    else:

        status = INVALID_TEMPERATURE

        logger.warning(
            "Invalid target temperature: %.1f°C. "
            "Valid range: 16.0°C - 30.0°C",
            requested_temperature / 10,
        )

    payload = SetTargetTemperatureResponsePayload(
        status
    ).serialize()

    return create_method_response(payload)


# ------------------------------------------------------------------
# Build provider service
# ------------------------------------------------------------------

def build_provider_service():

    get_temperature_method = Method(
        id=GET_CABIN_TEMPERATURE_METHOD_ID,
        protocol=TransportLayerProtocol.UDP,
        method_handler=get_cabin_temperature_handler,
    )

    set_temperature_method = Method(
        id=SET_TARGET_TEMPERATURE_METHOD_ID,
        protocol=TransportLayerProtocol.UDP,
        method_handler=set_target_temperature_handler,
    )

    provider_service = (
        ServiceBuilder()
        .with_service_id(CLIMATE_SERVICE_ID)
        .with_major_version(CLIMATE_MAJOR_VERSION)
        .with_method(get_temperature_method)
        .with_method(set_temperature_method)
        .with_eventgroup(cabin_temperature_eventgroup)
        .build()
    )

    return provider_service


# ------------------------------------------------------------------
# Simulate cabin temperature and publish events
# ------------------------------------------------------------------

async def simulate_cabin_temperature(service_instance):

    global current_cabin_temperature

    temperature_values = [240, 245, 250, 255, 260]
    index = 0

    while True:

        current_cabin_temperature = temperature_values[index]

        payload = CabinTemperaturePayload(
            current_cabin_temperature
        ).serialize()

        logger.info(
            "Publishing CabinTemperatureChanged: %.1f°C",
            current_cabin_temperature / 10,
        )

        service_instance.send_event(
            CABIN_TEMPERATURE_EVENTGROUP_ID,
            CABIN_TEMPERATURE_CHANGED_EVENT_ID,
            payload,
        )

        index = (index + 1) % len(temperature_values)

        await asyncio.sleep(3)


# ------------------------------------------------------------------
# Main application
# ------------------------------------------------------------------

async def main():

    set_someipy_log_level(logging.INFO)

    logger.info("Starting Climate ECU SOME/IP Provider")

    daemon = await connect_to_someipy_daemon()

    provider_service = build_provider_service()

    service_instance = ServerServiceInstance(
        daemon=daemon,
        service=provider_service,
        instance_id=CLIMATE_INSTANCE_ID,
        endpoint_ip="127.0.0.1",
        endpoint_port=3001,
        ttl=5,
        cyclic_offer_delay_ms=2000,
    )

    await service_instance.start_offer()

    logger.info("ClimateService offered successfully")
    logger.info("Service ID: 0x%04X", CLIMATE_SERVICE_ID)
    logger.info("Provider endpoint: 127.0.0.1:3001")

    temperature_task = asyncio.create_task(
        simulate_cabin_temperature(service_instance)
    )

    try:
        await asyncio.Future()

    finally:

        logger.info("Stopping Climate ECU Provider")

        temperature_task.cancel()

        try:
            await temperature_task
        except asyncio.CancelledError:
            logger.info("Temperature simulation stopped")

        await service_instance.stop_offer()
        await daemon.disconnect()


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    asyncio.run(main())

