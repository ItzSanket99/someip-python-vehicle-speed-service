
"""
Vehicle ECU - SOME/IP Service Provider.

Provides:
1. GetSpeed method (request-response)
2. SpeedChanged event (publish-subscribe)
"""

import asyncio
import logging
from typing import Tuple

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

from vehicle_speed_interface import (
    GET_SPEED_METHOD_ID,
    INSTANCE_ID,
    INTERFACE_IP,
    PROVIDER_PORT,
    SERVICE_ID,
    SPEED_CHANGED_EVENT_ID,
    SPEED_EVENTGROUP_ID,
    SpeedPayload,
    get_speed_method,
    speed_eventgroup,
)


# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Simulated vehicle speed
# ------------------------------------------------------------------

current_speed_kmph = 0


# ------------------------------------------------------------------
# GetSpeed method handler
# ------------------------------------------------------------------

async def get_speed_handler(
    input_data: bytes,
    client_address: Tuple[str, int],
) -> MethodResult:

    logger.info("GetSpeed request received")
    logger.info("Client address: %s", client_address)
    logger.info("Current vehicle speed: %d km/h", current_speed_kmph)

    # Convert current speed into SOME/IP payload bytes
    payload = SpeedPayload(current_speed_kmph).serialize()

    # Send method response
    return MethodResult(
        return_code=ReturnCode.E_OK,
        message_type=MessageType.RESPONSE,
        payload=payload,
    )


# ------------------------------------------------------------------
# Build provider service
# ------------------------------------------------------------------

def build_provider_service():

    get_speed_method = Method(
        id=GET_SPEED_METHOD_ID,
        protocol=TransportLayerProtocol.UDP,
        method_handler=get_speed_handler,
    )

    provider_service = (
        ServiceBuilder()
        .with_service_id(SERVICE_ID)
        .with_major_version(1)
        .with_method(get_speed_method)
        .with_eventgroup(speed_eventgroup)
        .build()
    )

    return provider_service


# ------------------------------------------------------------------
# Simulate speed and publish events
# ------------------------------------------------------------------

async def simulate_speed(service_instance):

    global current_speed_kmph

    while True:

        current_speed_kmph += 10

        if current_speed_kmph > 100:
            current_speed_kmph = 0

        payload = SpeedPayload(current_speed_kmph).serialize()

        logger.info(
            "Publishing SpeedChanged event: %d km/h",
            current_speed_kmph,
        )

        await service_instance.send_event(
            SPEED_EVENTGROUP_ID,
            SPEED_CHANGED_EVENT_ID,
            payload,
        )

        await asyncio.sleep(2)


# ------------------------------------------------------------------
# Main application
# ------------------------------------------------------------------

async def main():

    set_someipy_log_level(logging.INFO)

    logger.info("Starting Vehicle ECU SOME/IP Provider")

    # Connect to someipy daemon
    daemon = await connect_to_someipy_daemon()

    # Build service definition
    provider_service = build_provider_service()

    # Create server service instance
    service_instance = ServerServiceInstance(
        daemon=daemon,
        service=provider_service,
        instance_id=INSTANCE_ID,
        endpoint_ip=INTERFACE_IP,
        endpoint_port=PROVIDER_PORT,
        ttl=5,
        cyclic_offer_delay_ms=2000,
    )

    # Offer service to the network
    service_instance.start_offer()

    logger.info("VehicleSpeedService offered successfully")
    logger.info("Provider endpoint: %s:%d", INTERFACE_IP, PROVIDER_PORT)

    # Start periodic speed simulation
    speed_task = asyncio.create_task(
        simulate_speed(service_instance)
    )

    try:
        await asyncio.Future()

    finally:

        logger.info("Stopping Vehicle ECU Provider")

        speed_task.cancel()

        service_instance.stop_offer()

        await daemon.disconnect()


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        logger.info("Vehicle ECU Provider stopped")
