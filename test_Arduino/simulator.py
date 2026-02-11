import can
import time

bus = can.Bus(
    interface="slcan",
    channel="/dev/tty.usbserial-1130",  # ĐÚNG PORT
    bitrate=250000
)

msg = can.Message(
    arbitration_id=0x0CF00400,
    data=[0x00, 0xFA, 0x64, 0x00, 0, 0, 0, 0],
    is_extended_id=True
)

while True:
    bus.send(msg)
    print("ECU frame sent")
    time.sleep(0.1)
