'''
    Universidade Federal de Minas Gerais
    Redes de Computadores
    TP2 - DCCRIP
    Deiziane Natani da Silva
    2015121980
'''

import sys, json, copy, threading
import socket as sck
from random import randint

MAX_PAYLOAD_SIZE = 65536
MAX_HISTORY_VERSION = 10000


class Router:
    neighbors_table = []
    routing_table = []
    history_table = []

    # Construtor
    def __init__(self, ip, period):
        self.ip = ip
        self.port = 55151
        self.period = period
        this_routing = dict()
        this_routing['ip'] = ip
        this_routing['distance'] = 0
        this_routing['next'] = ip
        this_routing['ttl'] = 4
        self.history_table.append(this_routing)
        self.history_version = 0
        self.routing_version = 0
        self.routing_table = dict()
        self.update_routing_table()

    def add_neighbor(self, neighbor_ip, neighbor_weight):
        new_neighbor = dict()
        new_neighbor['ip'] = neighbor_ip
        new_neighbor['weight'] = int(neighbor_weight)
        self.neighbors_table.append(new_neighbor)
        new_route = dict()
        new_route['ip'] = new_neighbor['ip']
        new_route['distance'] = new_neighbor['weight']
        new_route['next'] = new_neighbor['ip']
        new_route['ttl'] = 4
        self.history_table.append(new_route)
        self.history_version = self.history_version + 1

    def remove_neighbor(self, neighbor_ip):
        to_remove = list(filter(lambda neighbor: neighbor['ip'] == neighbor_ip, self.neighbors_table))
        if len(to_remove) > 0:
            learned_from_neighbor = list(filter(lambda option: option['next'] == neighbor_ip, self.history_table))

            # remove rotas aprendidas por aquela vizinhança
            if len(learned_from_neighbor) > 0:
                for route in learned_from_neighbor:
                    self.history_table.remove(route)

            # update history version
            self.history_version = self.history_version + 1

            # remove vizinhança
            self.neighbors_table.remove(to_remove[0])

    def send_update(self):
        routing_table = self.get_routing_table()

        update_message = dict()
        update_message['type'] = 'update'
        update_message['source'] = self.ip
        update_message['destination'] = ''
        update_message['distances'] = dict()

        for ip in routing_table.keys():
            update_message['distances'][ip] = routing_table[ip][0]['distance']

        connection = sck.socket(sck.AF_INET, sck.SOCK_DGRAM)
        for neighbor in self.neighbors_table:
            # copia mensagem para usar a original em outra vizinhança
            copy_message = copy.deepcopy(update_message)
            copy_message['destination'] = neighbor['ip']

            # split horizon, remove rota para o destino da mensagem
            if neighbor['ip'] in copy_message['distances'].keys():
                del copy_message['distances'][neighbor['ip']]

            # split horizon, remove rota aprendida do destino da mensagem
            to_remove = []
            for ip in routing_table.keys():
                learned_from_destination = list(filter(lambda option: option['next'] == neighbor['ip'],
                                                       routing_table[ip]))
                if len(learned_from_destination) > 0 and ip in copy_message['distances'].keys():
                    to_remove.append(ip)
            for ip in to_remove:
                copy_message['distances'].pop(ip)

            # todas as rotas tem a mesma porta
            connection.sendto(json.dumps(copy_message).encode(), (neighbor['ip'], self.port))

    # atualiza tabela de roteamento por demanda
    def get_routing_table(self):
        if self.routing_version < self.history_version:
            # atualiza a tabela de roteamento
            self.update_routing_table()
        return self.routing_table

    # pega a melhor opção de rotas para cada IP
    # cada uma pode ter mais que uma rota com a mesma distancia (balanceamento de carga)
    def update_routing_table(self):
        routes_by_ip = dict()

        # extrai rotas da tabela de histórico
        for history in self.history_table:
            ip_key = history['ip']
            # caso não haja uma rota para o IP na tabela de roteamento
            # ou a tabela de histórico tenha uma rota com distância menor, atualiza a entrada da tabela de roteamento
            if ip_key not in routes_by_ip.keys() or routes_by_ip[ip_key][0]['distance'] > history['distance']:
                routes_by_ip[ip_key] = [history]
            elif routes_by_ip[ip_key][0]['distance'] == history['distance']:
                # caso haja uma rota para o IP com a mesma distancia, adiciona nova opção
                routes_by_ip[ip_key].append(history)

        self.routing_version = self.history_version
        self.routing_table = routes_by_ip

    def subtract_ttl(self, source_ip):
        to_remove = []
        # subtrai TTL das rotas aprendidas pela fonte
        for route in self.history_table:
            if route['next'] == source_ip:
                route['ttl'] = route['ttl'] - 1
                if route['ttl'] == 0:
                    to_remove.append(route)

        # remove rotas com TTL = 0 (rotas desatualizadas)
        for zero_ttl in to_remove:
            self.history_table.remove(zero_ttl)

    def receive_table_info(self, table_info):
        # encontra a vizinhança que enviou a informação
        source = list(filter(lambda neighbor: neighbor['ip'] == table_info['source'], self.neighbors_table))
        if len(source) == 0 or table_info['destination'] != self.ip:
            # retorna caso tenha uma fonte desconhecida ou outro destino
            return
        source = source[0]

        self.subtract_ttl(source['ip'])

        for ip in table_info['distances'].keys():
            # atualiza a tabela de historico
            on_history = list(filter(lambda route: route['ip'] == ip and route['next'] == table_info['source'],
                                     self.history_table))
            if len(on_history) > 0:
                on_history[0]['distance'] = table_info['distances'][ip] + source['weight']
                on_history[0]['ttl'] = 4
            else:
                new_history = dict()
                new_history['ip'] = ip
                new_history['distance'] = table_info['distances'][ip] + source['weight']
                new_history['next'] = table_info['source']
                new_history['ttl'] = 4
                self.history_table.append(new_history)

        self.history_version = self.history_version + 1
        if self.history_version > MAX_HISTORY_VERSION:
            self.history_version = 0
            self.update_routing_table()

    def receive_trace(self, message):
        # adiciona IPs para os hops
        message['hops'].append(self.ip)

        if message['destination'] != self.ip:
            self.send_message(message)
        else:
            self.send_data(message['source'], json.dumps(message['hops']))
    
    def receive_table(self, message):
        if message['destination'] != self.ip:
            self.send_message(message)
        else:
            routing_table = self.get_routing_table()
            payload = [] 
            for ip in routing_table.keys():
                    payload.append(tuple((routing_table[ip][0]['ip'], routing_table[ip][0]['next'], routing_table[ip][0]['distance'])))
                    
            self.send_data(message['source'], json.dumps(payload))

    def receive_data(self, message):
        if message['destination'] == self.ip:
            print(message['payload'])
        else:
            self.send_message(message)

    def send_trace(self, final_ip):
        trace_message = dict()
        trace_message['type'] = 'trace'
        trace_message['source'] = self.ip
        trace_message['destination'] = final_ip
        trace_message['hops'] = [self.ip]

        self.send_message(trace_message)

    def send_data(self, destination, payload):
        data_message = dict()
        data_message['type'] = 'data'
        data_message['source'] = self.ip
        data_message['destination'] = destination
        data_message['payload'] = payload

        self.send_message(data_message)
    
    def send_table(self, destination):
        table_message = dict()
        table_message['type'] = 'table'
        table_message['source'] = self.ip
        table_message['destination'] = destination

        self.send_message(table_message)


    def send_message(self, message):
        routing_table = self.get_routing_table()

        if message['destination'] in routing_table.keys():
            # seleciona uma das melhores opções de rota (balanceamento de carga)
            options = routing_table[message['destination']]
            selected_option = randint(0, len(options) - 1)
            selected_hop = options[selected_option]['next']

            connection = sck.socket(sck.AF_INET, sck.SOCK_DGRAM)
            # todos os roteadores tem a mesma porta
            connection.sendto(json.dumps(message).encode(), (selected_hop, self.port))


router = None


# chama function a cada 'secs' segundos
def set_interval(func, secs):
    def function_wrapper():
        func()
        set_interval(func, secs)
    t = threading.Timer(secs, function_wrapper)
    t.start()
    return t


def init_router(address, update_period, startup_commands):
    global router
    router = Router(address, update_period)

    socket = sck.socket(sck.AF_INET, sck.SOCK_DGRAM)
    socket.setsockopt(sck.SOL_SOCKET, sck.SO_REUSEADDR, 1)
    socket.bind((router.ip, router.port))

    if startup_commands:
        read_cmd_file(startup_commands)

    read_thread = threading.Thread(target=read_commands, args=())
    read_thread.start()

    read_thread = threading.Thread(target=receive_data, args=(socket,))
    read_thread.start()

    # envia mensagens de update para os vizinhos
    set_interval(router.send_update, router.period)


def read_cmd_file(file_name):
    with open(file_name, 'r') as file:
        line = file.readline()
        while line:
            if line is not '\n':
                read_command(line)
            line = file.readline()


def read_commands():
    while True:
        read = input()
        read_command(read)


def read_command(read_line):
    global router

    read_line = read_line.split()
    if read_line[0] == 'add':
        router.add_neighbor(read_line[1], read_line[2])
    elif read_line[0] == 'del':
        router.remove_neighbor(read_line[1])
    elif read_line[0] == 'trace':
        router.send_trace(read_line[1])
    elif read_line[0] == 'table':
        router.send_table(read_line[1])

def receive_data(connection):
    global router

    while True:
        data = json.loads(connection.recv(MAX_PAYLOAD_SIZE))

        if data['type'] == 'update':
            router.receive_table_info(data)
        elif data['type'] == 'trace':
            router.receive_trace(data)
        elif data['type'] == 'data':
            router.receive_data(data)
        elif data['type'] == 'table':
            router.receive_table(data)


def main():
    address = None
    update_period = None
    startup_commands = None

    if len(sys.argv) < 5:
        address = sys.argv[1]
        update_period = sys.argv[2]
        if len(sys.argv) > 3:
            startup_commands = sys.argv[3]
    else:
        if '--addr' in sys.argv:
            address = sys.argv[sys.argv.index('--addr') + 1]
        if '--update-period' in sys.argv:
            update_period = sys.argv[sys.argv.index('--update-period') + 1]
        if '--startup-commands' in sys.argv:
            startup_commands = sys.argv[sys.argv.index('--startup-commands') + 1]

    init_router(address, int(update_period), startup_commands)

    return


if __name__ == '__main__':
    main()