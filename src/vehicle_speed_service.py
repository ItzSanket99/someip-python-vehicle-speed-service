
"""
Vehicle ECU - SOME/IP Service Provider.

Provides:
1. GetSpeed method (request-response)
2. GetVehicleState method (request-response)
3. SpeedChanged event (publish-subscribe)
4. OverspeedWarning event (publish-subscribe)
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

from vehicle_speed_interface import (
    GET_SPEED_METHOD_ID,
    GET_VEHICLE_STATE_METHOD_ID,
    INSTANCE_ID,
    INTERFACE_IP,
    OVERSPEED_LIMIT_KMPH,
    OVERSPEED_WARNING_EVENT_ID,
    OVERSPEED_EVENTGROUP_ID,
    PROVIDER_PORT,
    SERVICE_ID,
    SPEED_CHANGED_EVENT_ID,
    SPEED_EVENTGROUP_ID,
    VEHICLE_MOVING,
    VEHICLE_STOPPED,
    SpeedPayload,
    VehicleStatePayload,
    speed_eventgroup,
    overspeed_eventgroup,
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
# Helper: Create SOME/IP method response
# ------------------------------------------------------------------

def create_method_response(payload):

    result = MethodResult()
    result.message_type = MessageType.RESPONSE
    result.return_code = ReturnCode.E_OK
    result.payload = payload

    return result


# ------------------------------------------------------------------
# GetSpeed method handler
# ------------------------------------------------------------------

async def get_speed_handler(input_data, client_address):

    logger.info("GetSpeed request received from %s", client_address)
    logger.info("Current vehicle speed: %d km/h", current_speed_kmph)

    payload = SpeedPayload(current_speed_kmph).serialize()

    return create_method_response(payload)


# ------------------------------------------------------------------
# GetVehicleState method handler
# ------------------------------------------------------------------

async def get_vehicle_state_handler(input_data, client_address):

    logger.info("GetVehicleState request received from %s", client_address)

    if current_speed_kmph > 0:
        vehicle_state = VEHICLE_MOVING
        state_name = "MOVING"
    else:
        vehicle_state = VEHICLE_STOPPED
        state_name = "STOPPED"

    logger.info("Current vehicle state: %s", state_name)

    payload = VehicleStatePayload(vehicle_state).serialize()

    return create_method_response(payload)


# ------------------------------------------------------------------
# Build provider service
# ------------------------------------------------------------------

def build_provider_service():

    get_speed_method = Method(
        id=GET_SPEED_METHOD_ID,
        protocol=TransportLayerProtocol.UDP,
        method_handler=get_speed_handler,
    )

    get_vehicle_state_method = Method(
        id=GET_VEHICLE_STATE_METHOD_ID,
        protocol=TransportLayerProtocol.UDP,
        method_handler=get_vehicle_state_handler,
    )

    provider_service = (
        ServiceBuilder()
        .with_service_id(SERVICE_ID)
        .with_major_version(1)
        .with_method(get_speed_method)
        .with_method(get_vehicle_state_method)
        .with_eventgroup(speed_eventgroup)
        .with_eventgroup(overspeed_eventgroup)
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

        # Publish SpeedChanged event
        speed_payload = SpeedPayload(current_speed_kmph).serialize()

        logger.info(
            "Publishing SpeedChanged event: %d km/h",
            current_speed_kmph,
        )

        logger.info("Before sending SpeedChanged event")

        service_instance.send_event(
            SPEED_EVENTGROUP_ID,
            SPEED_CHANGED_EVENT_ID,
            speed_payload,
        )

        logger.info("After sending SpeedChanged event")

        # Publish OverspeedWarning when speed exceeds 80 km/h
        if current_speed_kmph > OVERSPEED_LIMIT_KMPH:

            overspeed_payload = SpeedPayload(current_speed_kmph).serialize()

            logger.warning(
                "OVERSPEED WARNING! Current speed: %d km/h",
                current_speed_kmph,
            )

            service_instance.send_event(
                OVERSPEED_EVENTGROUP_ID,
                OVERSPEED_WARNING_EVENT_ID,
                overspeed_payload,
            )

        await asyncio.sleep(2)


# ------------------------------------------------------------------
# Main application
# ------------------------------------------------------------------

async def main():

    set_someipy_log_level(logging.INFO)

    logger.info("Starting Vehicle ECU SOME/IP Provider")

    # Connect to SOME/IP daemon
    daemon = await connect_to_someipy_daemon()

    # Build extended service definition
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

    # Offer service
    await service_instance.start_offer()

    logger.info("VehicleSpeedService offered successfully")
    logger.info("Provider endpoint: %s:%d", INTERFACE_IP, PROVIDER_PORT)

    # Start speed simulation
    speed_task = asyncio.create_task(
        simulate_speed(service_instance)
    )

    try:
        await asyncio.Future()

    finally:
        logger.info("Stopping Vehicle ECU Provider")

        speed_task.cancel()

        try:
            await speed_task
        except asyncio.CancelledError:
            logger.info("Speed simulation stopped")

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

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        logger.info("Vehicle ECU Provider stopped")
