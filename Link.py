import Packet

all_links = []
weights = {}


def remove_link(first, second):
    link = get_link_by_routers(first, second)
    weights[first, second] = link.cost
    all_links.remove(link)


def get_link_by_routers(first, second):
    for link in all_links:

        if (link.first_router.id == first.id and link.second_router.id == second.id) or (
                link.first_router.id == second.id and link.second_router.id == first.id):
            return link
    return None


class Link:

    def __init__(self, first_router, second_router, cost, state):
        self.first_router = first_router
        self.second_router = second_router
        self.cost = cost
        self.state = state
        all_links.append(self)

    def transfer_packet(self, first_router, second_router, packet):
        if self.state == 'Up':
            second_router.setup_connection(packet)
        if self.state == 'Down' and packet.packet_type == 'ping':
            print('link down')
