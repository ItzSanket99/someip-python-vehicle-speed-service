
"""
Central Display ECU - SOME/IP Consumer.

Consumes:
1. VehicleSpeedService
2. ClimateService

Features:
- Vehicle speed and state
- SpeedChanged and OverspeedWarning events
- Cabin temperature
- Set target temperature
- CabinTemperatureChanged event
- Independent service availability monitoring
"""

import asyncio
import logging

from someipy import (
    ClientServiceInstance,
    MessageType,
    ReturnCode,
    connect_to_someipy_daemon,
)

from someipy.someipy_logging import set_someipy_log_level

from vehicle_speed_interface import (
    SERVICE_ID,
    INSTANCE_ID,
    INTERFACE_IP,
    CONSUMER_PORT,
    GET_SPEED_METHOD_ID,
    GET_VEHICLE_STATE_METHOD_ID,
    SPEED_CHANGED_EVENT_ID,
    OVERSPEED_WARNING_EVENT_ID,
    SpeedPayload,
    VehicleStatePayload,
    speed_eventgroup,
    overspeed_eventgroup,
    vehicle_speed_service,
)

from climate_interface import (
    CLIMATE_SERVICE_ID,
    CLIMATE_INSTANCE_ID,
    GET_CABIN_TEMPERATURE_METHOD_ID,
    SET_TARGET_TEMPERATURE_METHOD_ID,
    CABIN_TEMPERATURE_CHANGED_EVENT_ID,
    CABIN_TEMPERATURE_EVENTGROUP_ID,
    ACCEPTED,
    INVALID_TEMPERATURE,
    CabinTemperaturePayload,
    TargetTemperaturePayload,
    SetTargetTemperatureResponsePayload,
    cabin_temperature_eventgroup,
    climate_service,
)


logger = logging.getLogger(__name__)

CLIMATE_CONSUMER_PORT = 3004

vehicle_available = False
climate_available = False


# ------------------------------------------------------------------
# Vehicle event callback
# ------------------------------------------------------------------

def vehicle_event_callback(event_id: int, event_payload: bytes):

    try:

        if event_id == SPEED_CHANGED_EVENT_ID:

            message = SpeedPayload().deserialize(event_payload)

            print(
                f"\n[Vehicle] SpeedChanged: "
                f"{message.speed_kmph.value} km/h"
            )

        elif event_id == OVERSPEED_WARNING_EVENT_ID:

            message = SpeedPayload().deserialize(event_payload)

            print("\n" + "=" * 50)
            print("[Vehicle] !!! OVERSPEED WARNING !!!")
            print(f"Speed: {message.speed_kmph.value} km/h")
            print("=" * 50)

    except Exception as error:
        logger.error("Vehicle event decoding failed: %s", error)


# ------------------------------------------------------------------
# Climate event callback
# ------------------------------------------------------------------

def climate_event_callback(event_id: int, event_payload: bytes):

    try:

        if event_id == CABIN_TEMPERATURE_CHANGED_EVENT_ID:

            message = CabinTemperaturePayload().deserialize(
                event_payload
            )

            print(
                f"\n[Climate] CabinTemperatureChanged: "
                f"{message.temperature.value / 10:.1f}°C"
            )

    except Exception as error:
        logger.error("Climate event decoding failed: %s", error)


# ------------------------------------------------------------------
# Vehicle method calls
# ------------------------------------------------------------------

async def call_vehicle_methods(client_instance):

    while True:

        try:

            if await client_instance.is_available():

                speed_result = await client_instance.call_method(
                    GET_SPEED_METHOD_ID,
                    b"",
                )

                if (
                    speed_result.message_type == MessageType.RESPONSE
                    and speed_result.return_code == ReturnCode.E_OK
                ):

                    speed = SpeedPayload().deserialize(
                        speed_result.payload
                    )

                    print(
                        f"\n[Vehicle] Current speed: "
                        f"{speed.speed_kmph.value} km/h"
                    )

                state_result = await client_instance.call_method(
                    GET_VEHICLE_STATE_METHOD_ID,
                    b"",
                )

                if (
                    state_result.message_type == MessageType.RESPONSE
                    and state_result.return_code == ReturnCode.E_OK
                ):

                    state = VehicleStatePayload().deserialize(
                        state_result.payload
                    ).state.value

                    state_name = (
                        "STOPPED" if state == 0
                        else "MOVING" if state == 1
                        else "UNKNOWN"
                    )

                    print(f"[Vehicle] State: {state_name}")

            else:
                print("\n[Vehicle] Service unavailable")

        except Exception as error:
            logger.error("Vehicle method call failed: %s", error)

        await asyncio.sleep(5)


# ------------------------------------------------------------------
# Climate method calls
# ------------------------------------------------------------------

async def call_climate_methods(client_instance):

    while True:

        try:

            if await client_instance.is_available():

                result = await client_instance.call_method(
                    GET_CABIN_TEMPERATURE_METHOD_ID,
                    b"",
                )

                if (
                    result.message_type == MessageType.RESPONSE
                    and result.return_code == ReturnCode.E_OK
                ):

                    temperature = CabinTemperaturePayload().deserialize(
                        result.payload
                    )

                    print(
                        f"\n[Climate] Cabin temperature: "
                        f"{temperature.temperature.value / 10:.1f}°C"
                    )

            else:
                print("\n[Climate] Service unavailable")

        except Exception as error:
            logger.error("Climate method call failed: %s", error)

        await asyncio.sleep(5)


# ------------------------------------------------------------------
# Set target temperature
# ------------------------------------------------------------------

async def set_target_temperature(client_instance, temperature):

    try:

        request = TargetTemperaturePayload(
            temperature
        ).serialize()

        result = await client_instance.call_method(
            SET_TARGET_TEMPERATURE_METHOD_ID,
            request,
        )

        if (
            result.message_type == MessageType.RESPONSE
            and result.return_code == ReturnCode.E_OK
        ):

            response = SetTargetTemperatureResponsePayload().deserialize(
                result.payload
            )

            status = response.status.value

            if status == ACCEPTED:

                print(
                    f"\n[Climate] Target temperature accepted: "
                    f"{temperature / 10:.1f}°C"
                )

            elif status == INVALID_TEMPERATURE:

                print(
                    f"\n[Climate] Invalid target temperature: "
                    f"{temperature / 10:.1f}°C"
                )

        else:
            print("[Climate] SetTargetTemperature request failed")

    except Exception as error:
        logger.error("SetTargetTemperature failed: %s", error)


# ------------------------------------------------------------------
# Monitor service availability independently
# ------------------------------------------------------------------

async def monitor_availability(vehicle_client, climate_client):

    global vehicle_available, climate_available

    while True:

        current_vehicle_status = await vehicle_client.is_available()
        current_climate_status = await climate_client.is_available()

        if current_vehicle_status != vehicle_available:

            vehicle_available = current_vehicle_status

            print(
                "\n[Vehicle] Service "
                + ("AVAILABLE" if vehicle_available else "UNAVAILABLE")
            )

        if current_climate_status != climate_available:

            climate_available = current_climate_status

            print(
                "\n[Climate] Service "
                + ("AVAILABLE" if climate_available else "UNAVAILABLE")
            )

        await asyncio.sleep(1)


# ------------------------------------------------------------------
# Main application
# ------------------------------------------------------------------

async def main():

    set_someipy_log_level(logging.INFO)

    print("=" * 60)
    print("CENTRAL DISPLAY ECU")
    print("=" * 60)

    daemon = await connect_to_someipy_daemon()

    print("Connected to SOME/IP daemon")

    # Vehicle service client
    vehicle_client = ClientServiceInstance(
        daemon=daemon,
        service=vehicle_speed_service,
        instance_id=INSTANCE_ID,
        endpoint_ip=INTERFACE_IP,
        endpoint_port=CONSUMER_PORT,
    )

    vehicle_client.register_callback(vehicle_event_callback)

    # Climate service client
    climate_client = ClientServiceInstance(
        daemon=daemon,
        service=climate_service,
        instance_id=CLIMATE_INSTANCE_ID,
        endpoint_ip=INTERFACE_IP,
        endpoint_port=CLIMATE_CONSUMER_PORT,
    )

    climate_client.register_callback(climate_event_callback)

    print("\nSearching independently for both services...")

    # Start monitoring both services independently.
    availability_task = asyncio.create_task(
        monitor_availability(vehicle_client, climate_client)
    )

    print("\nCentral Display is monitoring both services.")

    # Subscribe to event groups.
    # SOME/IP Service Discovery and subscription handling
    # will manage provider availability.

    vehicle_client.subscribe_eventgroup(speed_eventgroup, 5)
    vehicle_client.subscribe_eventgroup(overspeed_eventgroup, 5)

    climate_client.subscribe_eventgroup(
        cabin_temperature_eventgroup,
        5,
    )

    print("\nEvent-group subscription requests sent")

    # Subscribe to vehicle events
    vehicle_client.subscribe_eventgroup(speed_eventgroup, 5)
    vehicle_client.subscribe_eventgroup(overspeed_eventgroup, 5)

    # Subscribe to climate event
    climate_client.subscribe_eventgroup(
        cabin_temperature_eventgroup,
        5,
    )

    print("\nSubscribed to all event groups")

    # Start background tasks
    tasks = [
        availability_task,
        asyncio.create_task(
            call_vehicle_methods(vehicle_client)
        ),
        asyncio.create_task(
            call_climate_methods(climate_client)
        ),
    ]

    # Temperature validation tests
    await asyncio.sleep(2)

    test_temperatures = [220, 160, 300, 100, 350]

    for temperature in test_temperatures:

        await set_target_temperature(
            climate_client,
            temperature,
        )

        await asyncio.sleep(1)

    try:
        await asyncio.Future()

    finally:

        for task in tasks:
            task.cancel()

        for task in tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass

        await daemon.disconnect_from_daemon()


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        print("\nCentral Display stopped")
