import can.interface  # Import sâu vào module interface
from can.interfaces.pcan import PcanBus

try:
    print("Đang thử kết nối...")
    # Khởi tạo trực tiếp bằng class của PCAN để bỏ qua bước dò tìm interface
    bus = PcanBus(channel='PCAN_USBBUS1', bitrate=500000)
    print("Ngon rồi! Kết nối thành công.")
    bus.shutdown()
except Exception as e:
    print(f"Lỗi rồi đại ca: {e}")