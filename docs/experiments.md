
# Experiments

## 1. Introduction

This document records the experiments conducted for the Virtual Vehicle Speed Service Using SOME/IP mini-project.

The experiments demonstrate service discovery, method communication, event communication, and packet inspection using Wireshark.

## 2. Experiment Environment

| Parameter | Configuration |
|---|---|
| Operating System | Pop!_OS / Linux |
| Programming Language | Python |
| SOME/IP Library | someipy |
| Transport Protocol | UDP |
| Network Interface | Loopback (`lo`) |
| Provider IP | 127.0.0.1 |
| Provider Port | 3000 |
| Consumer IP | 127.0.0.1 |
| Consumer Port | 3002 |
| SD Multicast Address | 224.224.224.245 |
| SD Port | 30490 |

## 3. Experiment 1: Service Discovery

### Objective

To verify that the Instrument Cluster ECU can discover the VehicleSpeedService offered by the Vehicle ECU.

### Procedure

1. Start the SOME/IP daemon.
2. Start the Instrument Cluster ECU.
3. Start the Vehicle ECU.
4. Observe the consumer terminal.
5. Verify whether the service becomes available.

### Observation

The Instrument Cluster successfully discovered the VehicleSpeedService.

```text
VehicleSpeedService is AVAILABLE
```

### Result

**PASS** - Service Discovery was successfully verified.

## 4. Experiment 2: GetSpeed Method Communication

### Objective

To verify request-response communication between the Instrument Cluster ECU and Vehicle ECU.

### Procedure

1. Start the daemon.
2. Start the Vehicle ECU provider.
3. Start the Instrument Cluster consumer.
4. Allow the consumer to send GetSpeed requests.
5. Observe the response and payload.

### Observation

The consumer successfully received the current vehicle speed.

Example:

```text
Calling GetSpeed...

GetSpeed response received
Return code   : ReturnCode.E_OK
Payload bytes : 00 0a
Vehicle speed : 10 km/h
```

### Result

**PASS** - GetSpeed request-response communication was successfully verified.

## 5. Experiment 3: SpeedChanged Event Communication

### Objective

To verify publish-subscribe communication using the SpeedChanged event.

### Procedure

1. Start the SOME/IP daemon.
2. Start the Vehicle ECU provider.
3. Start the Instrument Cluster consumer.
4. Allow the consumer to subscribe to the SpeedChanged event group.
5. Observe the periodic event notifications.

### Observation

The consumer successfully received SpeedChanged event notifications.

Example:

```text
SpeedChanged notification received

Event ID      : 0x8001
Payload bytes : 00 14
Vehicle speed : 20 km/h
```

The speed value changes as the provider simulates vehicle speed.

### Result

**PASS** - SpeedChanged event subscription and notification reception were successfully verified.

## 6. Experiment 4: Wireshark Packet Inspection

### Objective

To capture and inspect SOME/IP communication packets using Wireshark.

### Procedure

1. Open Wireshark.
2. Select the loopback interface (`lo`).
3. Start packet capture.
4. Run the SOME/IP daemon, provider, and consumer.
5. Apply the following display filter:

```text
udp.port == 30490 || udp.port == 3000 || udp.port == 3002
```

6. Select a packet involving UDP ports 3000 and 3002.
7. Expand the UDP and SOME/IP Protocol sections.
8. Inspect the Service ID, Method ID, Message Type, Return Code, and payload.

### Observation

The captured packets were decoded by Wireshark as SOME/IP messages.

The GetSpeed request and response were identified using:

| Field | Observed Value |
|---|---|
| Service ID | 0x1234 |
| Method ID | 0x0001 |
| Request Message Type | 0x00 |
| Response Message Type | 0x80 |
| Response Return Code | 0x00 |

The response payload contains the two-byte vehicle speed value.

The SpeedChanged event was verified through the consumer's event notification logs. A separately decoded event packet should only be documented here after it has been identified in the capture.

### Result

**PASS** - SOME/IP method request and response packets were identified and inspected using Wireshark.

## 7. Additional Experiments

The following experiments are planned for additional runtime verification.

### Experiment 5: Start Consumer Before Provider

**Objective:** Observe service discovery when the consumer starts before the provider.

**Procedure:**

1. Start the daemon.
2. Start the consumer first.
3. Start the provider afterward.
4. Observe whether the consumer discovers the service.

**Observation:**

_To be recorded after performing the experiment._

**Result:** Pending.

### Experiment 6: Change Event Publishing Interval

**Objective:** Observe the effect of changing the event publishing interval.

**Procedure:**

1. Run the provider and consumer.
2. Temporarily change the event interval from 2 seconds to 1 second.
3. Observe the event notifications.
4. Compare the notification frequency.
5. Restore the original 2-second interval.

**Observation:**

_To be recorded after performing the experiment._

**Result:** Pending.

### Experiment 7: Restart the Provider

**Objective:** Observe consumer behaviour when the provider is restarted.

**Procedure:**

1. Start the daemon, provider, and consumer.
2. Stop the provider while the consumer is running.
3. Observe the consumer behaviour.
4. Restart the provider.
5. Check whether the consumer discovers the service again.

**Observation:**

_To be recorded after performing the experiment._

**Result:** Pending.

## 8. Overall Results

| Experiment | Status |
|---|---|
| Service Discovery | PASS |
| GetSpeed Method Communication | PASS |
| SpeedChanged Event Communication | PASS |
| Wireshark Method Packet Inspection | PASS |
| Consumer Before Provider | Pending |
| Event Interval Modification | Pending |
| Provider Restart | Pending |
