import networkx as nx
import threading
import Client
# from Client import time_elapsed
import Link
from Packet import Packet

all_routers = []
time_elapsed = 0

monitor_mode = False


def check_if_router_exist(router_id):
    for router in all_routers:
        if router.id == router_id:
            return True
    return False


def check_flood_tags():
    for router in all_routers:
        if router.flood_tag == False:
            return False
    return True


def get_router_by_id(id):
    for router in all_routers:
        if router.id == id:
            return router
    return None


def update_time():
    for router in all_routers:
        if router.state == 'Full':
            # print('eee')
            router.update_router_time()


class Router:

    def __init__(self, id):
        self.id = id
        self.state = 'Down'
        self.clients = []

        self.RT = {}
        self.LSDB = nx.Graph()
        self.received_packets = []
        self.neighbors = []
        self.current_time = time_elapsed
        self.LSDB.add_node(self)
        self.flood_tag = False
        self.neighbors_last_time = {}
        all_routers.append(self)

    def add_client(self, client):
        self.clients.append(client)

    def setup_connection(self, packet):
        dst_router = get_router_by_id(packet.dst_ip)
        if (len(self.clients) + len(self.neighbors)) >= 10 and packet.packet_type == 'start':
            print('all the interfaces are connected to routers.')
        else:
            if packet.packet_type == 'start':
                self.state = 'Init'
                new_packet = Packet(self.id, packet.dst_ip, 'first_hello', self.neighbors)
                dst_router.setup_connection(new_packet)


            else:
                packet_sender = get_router_by_id(packet.src_ip)
                if packet.packet_type == 'first_hello':
                    self.neighbors.append(packet_sender)
                    self.state = 'Init'
                    if monitor_mode:
                        print(str(self.id) + ': Hello packet received from router ' + str(packet.src_ip))
                    new_packet = Packet(self.id, packet_sender.id, 'first_hello_ack', self.neighbors)
                    packet_sender.setup_connection(new_packet)

                elif packet.packet_type == 'first_hello_ack':

                    for neighbor in packet_sender.neighbors:
                        if self.id == neighbor.id:
                            self.state = '2-way'
                            if monitor_mode:
                                print(str(self.id) + ': Hello packet received from router ' + str(packet.src_ip))
                            self.neighbors.append(packet_sender)
                            new_packet = Packet(self.id, packet_sender.id, 'final_hello', self.neighbors)
                            packet_sender.setup_connection(new_packet)


                elif packet.packet_type == 'final_hello':
                    for neighbor in packet_sender.neighbors:
                        if self.id == neighbor.id:
                            self.state = '2-way'
                            new_packet = Packet(self.id, packet_sender.id, 'final_hello_ack', self.neighbors)
                            packet_sender.setup_connection(new_packet)

                elif packet.packet_type == 'final_hello_ack':
                    self.state = 'Full'
                    new_packet = Packet(self.id, packet_sender.id, 'LSDB_update', self.neighbors)
                    packet_sender.setup_connection(new_packet)

                elif packet.packet_type == 'LSDB_update':
                    if monitor_mode:
                        print(str(self.id) + ': DBD packet received from router ' + str(packet.src_ip))
                    self.LSDB.update(packet_sender.LSDB)

                    self.state = 'Full'
                    new_packet = Packet(self.id, packet_sender.id, 'LSDB_update_ack', self.neighbors)
                    packet_sender.setup_connection(new_packet)

                elif packet.packet_type == 'LSDB_update_ack':
                    if monitor_mode:
                        print(str(self.id) + ': DBD packet received from router ' + str(packet.src_ip))
                    self.LSDB.update(packet_sender.LSDB)

                    self.state = 'Full'
                elif packet.packet_type == 'liveness_packet':
                    if monitor_mode:
                        print(str(self.id) + ': liveness packet received from router ' + str(packet.src_ip))
                    self.neighbors_last_time[get_router_by_id(packet.src_ip)] = time_elapsed

                elif packet.packet_type == 'flood_packet':

                    if monitor_mode:
                        print(str(self.id) + ': LSA packet received from router ' + str(packet.src_ip))

                    self.LSDB.update(get_router_by_id(packet.src_ip).LSDB)
                    self.update_RT()


                elif packet.packet_type == 'update':
                    self.update_RT()
                    self.flood()

                elif packet.packet_type == 'ping':
                    if monitor_mode and self.id != packet.src_ip:
                        print(str(self.id) + ': Ping packet received from router ' + str(packet.src_ip))
                    dest_router = packet.msg.router
                    if self.id == dest_router.id and packet.msg in self.clients:
                        print(str(self.id) + ' ' + packet.msg.ip)
                        return
                    print(str(self.id), end=' ')

                    found = False
                    unreachable_flag = False
                    for key in self.RT:
                        if dest_router.id == key.id:
                            unreachable_flag = True
                            if Link.get_link_by_routers(self, self.RT[key]) is not None:

                                link = Link.get_link_by_routers(self, self.RT[key])
                                ping_packet = Packet(self.id, self.RT[key].id, 'ping', packet.msg)
                                link.transfer_packet(self, self.RT[key], ping_packet)
                                found = True

                            else:
                                print('unreachable')

                    if found is False and unreachable_flag is False:
                        print('invalid')

    def update_router_time(self):
        self.check_neighbors_aliveness()
        if (time_elapsed - self.current_time) >= 10:
            for neighbor in self.neighbors:
                if Link.get_link_by_routers(self, neighbor) is not None:
                    liveness_packet = Packet(self.id, neighbor.id, 'liveness_packet',
                                             Link.get_link_by_routers(self, neighbor))
                    Link.get_link_by_routers(self, neighbor).transfer_packet(self, neighbor, liveness_packet)

            self.current_time = time_elapsed

    def set_neighbors_last_time(self):
        for neighbor in self.neighbors:
            if neighbor not in self.neighbors_last_time.keys():
                self.neighbors_last_time[neighbor] = 0

    def check_neighbors_aliveness(self):
        self.set_neighbors_last_time()
        for neighbor in self.neighbors:
            if (time_elapsed - self.neighbors_last_time[neighbor]) >= 30:
                if Link.get_link_by_routers(self, neighbor) is not None:
                    # Link.remove_link(self, neighbor)
                    # self.LSDB.remove_edge(self, neighbor)
                    # self.neighbors.remove(neighbor)
                    # update_packet = Packet(self.id, neighbor.id, 'update', None)
                    # self.setup_connection(update_packet)

                    Link.remove_link(self, neighbor)
                    self.LSDB.remove_edge(self, neighbor)
                    self.LSDB.add_edge(self, neighbor, weight=10000)
                    update_packet = Packet(self.id, self.id, 'update', None)
                    self.setup_connection(update_packet)

    def flood(self):
        for router in all_routers:
            if router != self:
                flood_packet = Packet(self.id, router.id, 'flood_packet', None)
                router.flood_tag = True

                router.setup_connection(flood_packet)

    def update_RT(self):
        for router in all_routers:
            if router != self:
                try:
                    next_router = nx.dijkstra_path(self.LSDB, self, router)[1]
                    self.RT[router] = next_router
                except nx.NetworkXNoPath as e:
                    pass
