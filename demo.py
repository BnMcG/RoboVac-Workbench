from Crypto.Cipher import AES
import struct

from google.protobuf.message import DecodeError

import protocol.LocalServerInfo_pb2
import socket
import random

ROBOVAC_IP = ''
ROBOVAC_PORT = 55556
ROBOVAC_LOCAL_CODE = ''

aes_key = bytearray([0x24, 0x4E, 0x6D, 0x8A, 0x56, 0xAC, 0x87, 0x91, 0x24, 0x43, 0x2D, 0x8B, 0x6C, 0xBC, 0xA2, 0xC4])
aes_iv = bytearray([0x77, 0x24, 0x56, 0xF2, 0xA7, 0x66, 0x4C, 0xF3, 0x39, 0x2C, 0x35, 0x97, 0xE9, 0x3E, 0x57, 0x47])


class RoboVacStatus:
    def __init__(self,
                 find_me,
                 water_tank_status,
                 mode,
                 speed,
                 charger_status,
                 battery_capacity,
                 error_code,
                 stop):
        self.find_me = find_me
        self.water_tank_status = water_tank_status
        self.mode = mode
        self.speed = speed
        self.charger_status = charger_status
        self.battery_capacity = battery_capacity
        self.error_code = error_code
        self.stop = stop

    def __str__(self) -> str:
        return f'[FIND_ME: {self.find_me}, WATER_TANK: {self.water_tank_status}, MODE: {self.mode}, SPEED: {self.speed}, CHARGER_STATUS: {self.charger_status}, BATTERY_CAPACITY: {self.battery_capacity}, ERROR_CODE: {self.error_code}, STOP: {self.stop}]'


def send_packet(sock, packet, receive: bool):
    raw_packet = packet.SerializeToString()
    # Pad to 16 bit interval for AES CBC
    for i in range(16 - (len(raw_packet) % 16)):
        raw_packet += b'\0'

    cipher = AES.new(bytes(aes_key), AES.MODE_CBC, bytes(aes_iv))
    encrypted_packet = cipher.encrypt(raw_packet)

    sock.send(encrypted_packet)

    if not receive:
        return None

    response_packet = sock.recv(1024)
    response_cipher = AES.new(bytes(aes_key), AES.MODE_CBC, bytes(aes_iv))
    decrypted_packet = response_cipher.decrypt(response_packet)
    length = struct.unpack("<H", decrypted_packet[0:2])[0]
    protobuf_data = decrypted_packet[2:length + 2]

    try:
        response_message = LocalServerInfo_pb2.LocalServerMessage()
        response_message.ParseFromString(protobuf_data)
        return response_packet.hex(), response_message
    except DecodeError:
        return decrypted_packet.hex(), None


def get_magic_num(sock):
    # Construct ping packet
    ping_packet = LocalServerInfo_pb2.LocalServerMessage()
    ping_packet.a.type = 0
    ping_packet.localcode = ROBOVAC_LOCAL_CODE
    ping_packet.magic_num = random.randrange(3000000)

    print(f'Sending magic number of {ping_packet.magic_num}')

    # Send ping and get ping response from Robovac, this will contain the
    # magic number to use.
    hex, ping_response = send_packet(sock, ping_packet, True)

    if ping_response.a.type == 1:
        current_magic_num = ping_response.magic_num
        # Increment by 1 for next message
        return current_magic_num + 1

    raise Exception("Cannot get magic number from Robovac. Invalid ping response")


def build_user_data_message(sock, data):
    magic_num = get_magic_num(sock)

    message = LocalServerInfo_pb2.LocalServerMessage()
    message.magic_num = magic_num
    message.localcode = ROBOVAC_LOCAL_CODE
    message.c.type = 0
    message.c.usr_data = data

    return message


def build_get_device_status_message(sock):
    magic_num = get_magic_num(sock)

    message = LocalServerInfo_pb2.LocalServerMessage()
    message.magic_num = magic_num
    message.localcode = ROBOVAC_LOCAL_CODE
    message.c.type = 1

    return message


# Mode and command should be individual bytes
def build_robovac_command(mode, command):
    mcu_ota_header_0xa5 = 0xA5
    # Guessing this is (mode + command) as 1 byte
    cmd_data = (mode + command) # (byte) (cmdData[1] + cmdData[2]) in Java, but cmdData not defined
    return bytes([mcu_ota_header_0xa5, mode, command, cmd_data, 0xFA])


def turn_left(sock):
    command = build_robovac_command(0xE4, 0x01)
    message = build_user_data_message(sock, command)
    send_packet(sock, message, False)


def turn_right(sock):
    command = build_robovac_command(0xE5, 0x01)
    message = build_user_data_message(sock, command)
    send_packet(sock, message, False)


def go_forward(sock):
    command = build_robovac_command(0xE2, 0x01)
    message = build_user_data_message(sock, command)
    send_packet(sock, message, False)


def go_backward(sock):
    command = build_robovac_command(0xE3, 0x01)
    message = build_user_data_message(sock, command)
    send_packet(sock, message, False)


def start_auto_mode(sock):
    command = build_robovac_command(0xE1, 0x02)
    message = build_user_data_message(sock, command)
    send_packet(sock, message, False)


def start_single_room_mode(sock):
    command = build_robovac_command(0xE1, 0x05)
    message = build_user_data_message(sock, command)
    send_packet(sock, message, False)


def start_spot_mode(sock):
    command = build_robovac_command(0xE1, 0x01)
    message = build_user_data_message(sock, command)
    send_packet(sock, message, False)


def start_edge_mode(sock):
    command = build_robovac_command(0xE1, 0x04)
    message = build_user_data_message(sock, command)
    send_packet(sock, message, False)


def set_speed(sock, speed):
    command = build_robovac_command(0xE8, speed)
    message = build_user_data_message(sock, command)
    send_packet(sock, message, False)


def go_home(sock):
    command = build_robovac_command(0xE1, 0x03)
    message = build_user_data_message(sock, command)
    send_packet(sock, message, False)


def stop_robot(sock):
    command = build_robovac_command(0xE1, 0x00)
    message = build_user_data_message(sock, command)
    send_packet(sock, message, False)


def find_robovac(sock, ring: bool):
    ring_toggle = 0x01
    if not ring:
        ring_toggle = 0x00

    command = build_robovac_command(0xEC, ring_toggle)
    message = build_user_data_message(sock, command)
    send_packet(sock, message, False)


def get_robovac_status(sock):
    message = build_get_device_status_message(sock)
    received_hex, received_message = send_packet(sock, message, True)
    received_status_array = received_message.c.usr_data

    received_status_ints = [x for x in received_status_array]

    return RoboVacStatus(
        1 if received_status_ints[6] & 4 > 0 else 0,
        1 if received_status_ints[6] & 2 > 0 else 0,
        received_status_ints[1] & 255,
        received_status_ints[8] & 255,
        received_status_ints[11] & 255,
        received_status_ints[10] & 255,
        received_status_ints[12] & 255,
        received_status_ints[13] & 255
    )


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((ROBOVAC_IP, ROBOVAC_PORT))
print(get_robovac_status(s))
s.close()
