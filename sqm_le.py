import time
import socket
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(module)s %(message)s")
log = logging.getLogger(__file__)


class SQM:
    def __init__(self, ip_address=None):
        self.found_device = False
        if ip_address is None:
            self.find_device()
        else:
            self.ip_address = ip_address

    def send_request(self, code="rx"):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.ip_address, 10001))
            s.send(code.encode())
            data = s.recv(1024).decode().replace("\r\n", "").split(",")
        return data

    def get_reading(self):
        data = self.send_request("rx")
        return float(data[1].strip()[:-1])

    def find_device(self, set_ip=True):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setblocking(False)
        message = b"\x00\x00\x00\xf6"
        if hasattr(socket, "SO_BROADCAST"):
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.sendto(message, ("255.255.255.255", 30718))
        starttime = time.time()
        addr = [None, None]
        while True:
            try:
                (buf, addr) = s.recvfrom(30)
                if buf[3].encode("hex") == "f7":
                    log.info(f"Received from {addr}: MAC: buf[24:30].encode('hex')")
            except:
                if time.time() - starttime > 3:  # timeout
                    break
                pass
        try:
            assert addr[0] != None
        except:
            log.warning("ERR. Device not found!")
            raise
        else:
            log.info(f"Found device at: {addr[0]}")
            if set_ip:
                self.ip_address = addr[0]
            self.found_device = True
            return addr[0]

    def __repr__(self):
        if self.found_device:
            return f"Verified SQM-LE found at {self.ip_address}"
        elif self.ip_address:
            return f"Unverified SQM-LE set to {self.ip_address}"
        else:
            return f"Uninitialized SQM-LE"
