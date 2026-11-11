
# Observations and Analysis

## 1. Introduction

This document contains the observations made during the implementation and verification of the Virtual Vehicle Speed Service using SOME/IP.

The project demonstrates service discovery, request-response communication, publish-subscribe communication, and SOME/IP packet inspection.

## 2. Service Discovery Observations

- The Vehicle ECU acts as the service provider.
- The Instrument Cluster ECU acts as the service consumer.
- The SOME/IP daemon handles communication and service discovery.
- The consumer successfully discovers the VehicleSpeedService.
- The service is identified using Service ID `0x1234` and Instance ID `0x5678`.

## 3. GetSpeed Method Observations

The GetSpeed method follows the request-response communication model.

The Instrument Cluster initiates the request, and the Vehicle ECU sends a response containing the current vehicle speed.

### Observed SOME/IP Parameters

| Parameter | Value |
|---|---|
| Service ID | 0x1234 |
| Method ID | 0x0001 |
| Request Message Type | 0x00 |
| Response Message Type | 0x80 |
| Return Code | 0x00 |
| Payload Size | 2 bytes |

### Payload Analysis

Example payload:

```text
00 0a
```

The payload is interpreted as an unsigned 16-bit big-endian integer.

```text
0x000A = 10 (decimal)
```

Therefore, the vehicle speed is 10 km/h.

Another example:

```text
00 64
```

```text
0x0064 = 100 (decimal)
```

Therefore, the vehicle speed is 100 km/h.

## 4. SpeedChanged Event Observations

The SpeedChanged event follows the publish-subscribe communication model.

The Instrument Cluster subscribes to the event group, and the Vehicle ECU periodically publishes updated speed values.

### Observed SOME/IP Parameters

| Parameter | Value |
|---|---|
| Service ID | 0x1234 |
| Event ID | 0x8001 |
| Event Group ID | 0x0001 |
| Payload Size | 2 bytes |
| Publishing Interval | 2 seconds |

### Example Event Payload

```text
00 14
```

The hexadecimal value `0x0014` represents decimal value `20`.

Therefore, the event indicates a vehicle speed of 20 km/h.

## 5. Method Communication vs Event Communication

| Feature | GetSpeed Method | SpeedChanged Event |
|---|---|---|
| Communication Model | Request-Response | Publish-Subscribe |
| Initiated By | Consumer | Provider publishes after subscription |
| Communication Direction | Request and response | Provider to subscribers |
| Method/Event ID | 0x0001 | 0x8001 |
| Purpose | Retrieve current speed | Receive periodic speed updates |
| Communication Pattern | On demand | Periodic notification |

### Key Observation

Method communication requires the consumer to send a request whenever it needs the current speed.

Event communication allows the consumer to receive updated speed information after subscribing to the event group.

## 6. Wireshark Observations

Wireshark was used to capture UDP traffic on the loopback interface.

### Display Filter

```text
udp.port == 30490 || udp.port == 3000 || udp.port == 3002
```

### GetSpeed Request

The request packet was observed travelling from the Instrument Cluster ECU to the Vehicle ECU.

| Field | Value |
|---|---|
| Source Port | 3002 |
| Destination Port | 3000 |
| Service ID | 0x1234 |
| Method ID | 0x0001 |
| Message Type | 0x00 (Request) |

### GetSpeed Response

The response packet was observed travelling from the Vehicle ECU to the Instrument Cluster ECU.

| Field | Value |
|---|---|
| Source Port | 3000 |
| Destination Port | 3002 |
| Service ID | 0x1234 |
| Method ID | 0x0001 |
| Message Type | 0x80 (Response) |
| Return Code | 0x00 (OK) |

### Event Notification

The consumer successfully received SpeedChanged notifications.

The event was identified in the application logs using Event ID `0x8001`.

## 7. Important Findings

1. SOME/IP enables service-oriented communication between virtual ECUs.
2. Service Discovery allows the consumer to discover the provider.
3. The GetSpeed method demonstrates request-response communication.
4. The SpeedChanged event demonstrates publish-subscribe communication.
5. The vehicle speed is transmitted as a two-byte payload.
6. Wireshark allows inspection of SOME/IP headers and payloads.
7. Both virtual ECUs can communicate over the loopback interface on the same Linux machine.

## 8. Conclusion

The implementation successfully demonstrates the basic concepts of SOME/IP communication using Python and the someipy library.

The Vehicle ECU provides vehicle speed information through the GetSpeed method and periodically publishes speed updates through the SpeedChanged event.

The Instrument Cluster ECU successfully discovers the service, requests vehicle speed, and receives event notifications.

Wireshark packet inspection provides additional understanding of the SOME/IP message structure and communication flow.
