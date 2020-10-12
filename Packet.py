class Packet:
    def __init__(self, src_ip, dst_ip, packet_type, msg):
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.packet_type = packet_type
        self.msg = msg
