import Router, Link
from Packet import Packet

all_clients = []


def get_client_by_ip(client_ip):
    for client in all_clients:
        if client.ip == client_ip:
            return client
    return None


class Client:

    def __init__(self, ip):
        self.ip = ip
        self.router = None
        all_clients.append(self)

    def set_router(self, router):
        self.router = router


if __name__ == '__main__':
    time_elapsed = 0
    while (True):
        command = input()
        splitted = command.split(' ')

        # "add router #"
        if splitted[0] == 'add' and splitted[1] == 'router':
            router_id = int(splitted[2])
            if not Router.check_if_router_exist(router_id):
                new_router = Router.Router(router_id)

        # "add client #"
        if splitted[0] == 'add' and splitted[1] == 'client':
            client_ip = splitted[2]
            if get_client_by_ip(client_ip) is None:
                new_client = Client(client_ip)

        if splitted[0] == 'sec':
            Router.time_elapsed += int(splitted[1])
            Router.update_time()

        # "connect client to router"
        if splitted[0] == 'connect' and '.' in splitted[1]:
            client_ip = splitted[1]
            router_id = int(splitted[2])
            router = None
            if Router.get_router_by_id(router_id) is not None:
                router = Router.get_router_by_id(router_id)
            if get_client_by_ip(client_ip) is not None:
                get_client_by_ip(client_ip).set_router(router)
                router.add_client(get_client_by_ip(client_ip))

        # "connect #x #y #n"

        if splitted[0] == 'connect' and '.' not in splitted[1]:
            first_id = int(splitted[1])
            second_id = int(splitted[2])
            link_cost = int(splitted[3])
            first_router = None
            second_router = None

            if (Router.get_router_by_id(first_id) is not None) and (Router.get_router_by_id(second_id) is not None):
                first_router = Router.get_router_by_id(first_id)
                second_router = Router.get_router_by_id(second_id)
            else:
                print('either 1st or 2nd router not existed in the network.')

            initial_packet = Packet(first_router.id, second_router.id, 'start', link_cost)
            first_router.setup_connection(initial_packet)
            if first_router.state == 'Full' and second_router.state == 'Full':
                new_link = Link.Link(first_router, second_router, link_cost, 'Up')

                first_router.LSDB.add_edge(first_router, second_router, weight=link_cost)

                update_packet = Packet(first_router.id, second_router.id, 'update', link_cost)
                first_router.setup_connection(update_packet)

        # "ping #1 #2"
        if splitted[0] == 'ping':
            first_client_ip = splitted[1]
            second_client_ip = splitted[2]
            first_client = None
            second_client = None
            if get_client_by_ip(first_client_ip) is not None and get_client_by_ip(second_client_ip) is not None:
                first_client = get_client_by_ip(first_client_ip)
                second_client = get_client_by_ip(second_client_ip)

            if first_client.router is not None and second_client.router is not None:
                print(first_client.ip, end=' ')
                ping_packet = Packet(first_client.router.id, second_client.router.id, 'ping', second_client)
                first_client.router.setup_connection(ping_packet)
            else:
                print('client:' + first_client.ip + 'is not connected to a router.')

        if splitted[0] == 'monitor':
            if splitted[1] == 'e':
                Router.monitor_mode = True
            elif splitted[1] == 'd':
                Router.monitor_mode = False

        if splitted[0] == 'link':
            first_id = int(splitted[1])
            second_id = int(splitted[2])
            first_router = Router.get_router_by_id(first_id)
            second_router = Router.get_router_by_id(second_id)
            if splitted[3] == 'd':
                if Link.get_link_by_routers(first_router, second_router) is not None:
                    Link.remove_link(first_router, second_router)
                    first_router.LSDB.remove_edge(first_router, second_router)
                    first_router.LSDB.add_edge(first_router, second_router, weight=10000)
                    update_packet = Packet(first_router.id, second_router.id, 'update', None)
                    first_router.setup_connection(update_packet)

                # for router in Router.all_routers:
                #     print('router no:' + str(router.id))
                #     for neigh in router.RT.keys():
                #         print(str(neigh.id) + ': way= ' + str(router.RT[neigh].id))

            if splitted[3] == 'e':
                if Link.get_link_by_routers(first_router, second_router) is None:
                    link_cost = Link.weights[first_router, second_router]
                    new_link = Link.Link(first_router, second_router, link_cost, 'Up')
                    first_router.LSDB.remove_edge(first_router, second_router)
                    first_router.LSDB.add_edge(first_router, second_router, weight=link_cost)
                    update_packet = Packet(first_router.id, second_router.id, 'update', link_cost)
                    first_router.setup_connection(update_packet)

        if splitted[0] == 'exit':
            break
