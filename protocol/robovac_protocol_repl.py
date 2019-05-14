from Crypto.Cipher import AES
import struct
import LocalServerInfo_pb2
import binascii

aes_key = bytearray([0x24, 0x4E, 0x6D, 0x8A, 0x56, 0xAC, 0x87, 0x91, 0x24, 0x43, 0x2D, 0x8B, 0x6C, 0xBC, 0xA2, 0xC4])
aes_iv = bytearray([0x77, 0x24, 0x56, 0xF2, 0xA7, 0x66, 0x4C, 0xF3, 0x39, 0x2C, 0x35, 0x97, 0xE9, 0x3E, 0x57, 0x47])

while True:
    packet = input("Encrypted packet > ")

    try:
        cipher = AES.new(bytes(aes_key), AES.MODE_CBC, bytes(aes_iv))
        decrypted_packet = cipher.decrypt(binascii.unhexlify(packet.replace(':', '')))
        length = struct.unpack("<H", decrypted_packet[0:2])[0]

        protobuf_data = decrypted_packet[2:length + 2]

        try:
            local_server_message = LocalServerInfo_pb2.LocalServerMessage()
            local_server_message.ParseFromString(protobuf_data)
            print(local_server_message)
        except Exception:
            pass
    except ValueError as v:
        print(str(v))
    print("--------")
