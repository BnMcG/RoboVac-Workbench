# Protocol reverse-engineering scripts and resources
This directory contains scripts and resources for reverse-engineering the Eufy RoboVac protcol.

## Protocol outline
All messages from the client must have a valid local code, which seems to be unique to each RoboVac.

Messages are encrypted using AES CBC. The IV and encryption keys are hard-coded into the app, and can be found in demo.py.

### Ping messages
Each 'transaction' with the RoboVac seems to start with a ping request from the mobile app. The ping message is a type of LocalServerMessage,
with two types: request and response.

The client send a ping request message, including the RoboVac's local code, and a random "magic number". It seems that this number
can be anything from 0 to 3,000,000. The server then responds with a ping response message. The ping response contains another magic number,
again seemingly random and unrelated to the magic number included in the ping request.

The client's next message to the RoboVac must include the magic number from the ping response, incremented by one. I assume this is to prevent
replay attacks on the RoboVac?

### Sending commands to the RoboVac
Commands to the RoboVac are enclosed in a UserDataMessage, which in turn is a type of LocalServerMessage. 

Commands to the RoboVac have a UserDataType of sendUsrDataToDev. They must include a magic number and local code. The command itself is sent in the usr_data field. 

The command format seems to be a sequence of bytes. The command
itself is made up of a (mode, command) tuplet. Each mode seems
to refer to different operations of the RoboVac (eg: start working, find robovac, move left, move right), while the command is the action to take (single room, auto, spot, etc). For example, to begin cleaning in spot mode, the following bytes are sent: `(0xE1, 0x01)`. `0xE1` is the work mode, while `0x01` relates to spot cleaning.

The commands actually sent to the RoboVac include some extra information, as an array in the following format:

```
[OTA_HEADER_BYTE, MODE, COMMAND, (MODE + COMMAND), 0xFA]
```

The `OTA_HEADER_BYTE` is a static value defined in the app, while the final `0xFA` byte also never changes.


### Receiving data from the RoboVac
The device status can be retrieved from the RoboVac. In order to do this, a User Data message is sent to the RoboVac, without any user data payload. The message must have a type of `getDevStatusData`. 

The RoboVac responds with a User Data message, this time with a type of `sendStausDataToApp` (The typo is also made in the Protobuf definition file). The user data payload contains a byte array that describes the RoboVac's current status.

An example of how to decode the byte array is included in demo.py.

## Protobuf
Protobuf definitions can be found in the protobuf/ directory. These will need to be compiled to a client for a language of your choice
using protoc. So far, only definitions from `LocalServerInfo.proto` seem to be used when communicating with a RoboVac

## Scripts

### robovac_protocol_repl.py
A simple REPL. You can pass in an encrypted packet received from a RoboVac device, and it will decrypt the packet and then attempt
to parse it into a `LocalServerMessage` and print the result. Useful for spying on messages received from a RoboVac that have been
sniffed on the LAN.

### robovac_wireshark_parser.py
Takes a JSON export of packets sniffed by Wireshark and parses the data from each packet. For each packet with data, it will attempt to
decrypt it, parse as a `LocalServerMessage`, and print the result. This can be used to try and decode an entire conversation between the mobile app and the RoboVac sniffed using Wireshark.

### LocalServerInfo_pb2.py
Compiled Protobuf definition for local server messages.