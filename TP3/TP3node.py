'''
Responsável pelo armazenamento da base de dados chave-valor 
e pelo controle da troca de mensagens com seus parceiros
'''
import sys
import socket
import struct
import select
import queue

class Servent:  # Class to represent each servent
    def __init__(self):
        params = len(sys.argv)
        self.ip = '127.0.0.1'  # Local host IP
        self.port = int(sys.argv[1])
        self.file = sys.argv[2]

        self.neighbors = list()
        for i in range(3, params):
            self.neighbors.append(sys.argv[i])

        self.key_values = {}
        self.key_values = self.keyDictionaryConstructor(self.file)
        self.createSocket()
        self.serventListConstructor()
    
    # Percorre a lista de vizinhos do servent e conecta a cada um deles
    def serventListConstructor(self):
        for neighbor in self.neighbors:
            connection_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connect_to_neighbor(connection_socket, neighbor)
            inputs.append(connection_socket)
            message_queues[connection_socket] = queue.Queue()

    def keyDictionaryConstructor(self, inputFile):
        try:
            file = open(inputFile, "r")
        except (OSError, IOError) as error:
            print("Erro ao abrir arquivo.")

        dictionary = {}
        for line in file:
            if not line.isspace(): # Linha nao vazia
                words = line.split()
                if words[0] != '#': # Primeira palavra da linha
                    first_character = str.strip(words[0][0])
                    if first_character != '#': # Verifica se o primeiro caracter nao e' #
                        key = str.strip(words[0])
                        text = words[1:]
                        value = ' '.join(text)
                        dictionary.update({ key : value })

        file.close()

        return dictionary
    

    def createSocket(self):
        servert_addr = (self.ip, self.port)
        self.servent_socket = self.set_servent_socket(servert_addr)
        self.servent_socket.listen()

    def set_servent_socket(self, servert_addr):
        # Realiza a configuracao do socket do servent principal
        self.servent_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.servent_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.servent_socket.setblocking(0)
        self.servent_socket.bind(servert_addr)

        return self.servent_socket


    def connect_to_neighbor(self, connection_socket, neighbor):
        # Conecta o servent ao vizinho
        neighbor_ip = neighbor.split(":")[0]
        neighbor_port = int(neighbor.split(":")[1])
        neighbor_addr = (neighbor_ip, neighbor_port)

        connection_socket.connect(neighbor_addr)
        connection_socket.setblocking(0)

        # Envia mensagem ID para o vizinho
        msg = Message.create_id_msg(0)
        connection_socket.send(msg)


class Message:
    #+---- 2 ---+--- 2 ---------------------------+
    #| TIPO = 4 |  PORTO (ou zero se for servent) |
    #+----------+---------------------------------+
    def create_id_msg(port):
        type = struct.pack("!H", 4)
        port = struct.pack("!H", port)

        msg = type + port

        return msg


    #+---- 2 ---+-- 4 -+--- 2 ---+---------------------------+
    #| TIPO = 5 | NSEQ | TAMANHO | CHAVE (ate 400 carateres) | 
    #+----------+------+---------+---------------------------+
    def create_keyreq_msg(nseq, key):
        type = struct.pack("!H", 5)
        nseq = struct.pack("!I", nseq)
        size = struct.pack("@H", len(key))

        msg = type + nseq + size + key.encode('ascii')

        return msg


    #+---- 2 ---+-- 4 -+
    #| TIPO = 6 | NSEQ |
    #+----------+------+
    def create_toporeq_msg(nseq):
        type = struct.pack("!H", 6)
        nseq = struct.pack("!I", nseq)

        msg = type + nseq

        return msg


    #+---- 2 ------+- 2 -+-- 4 -+--- 4 ---+----- 2 ----+--- 2 ---+--------------------------+ 
    #| TIPO = 7, 8 | TTL | NSEQ | IP_ORIG | PORTO_ORIG | TAMANHO | INFO (ate 400 carateres) | 
    #+-------------+-----+------+---------+------------+---------+--------------------------+
    def create_flood_message(servent, msg_type, ttl, nseq, src_port, info):
        
        if msg_type == 7:
            type = struct.pack("!H", 7)
        else:
            type = struct.pack("!H", 8)

        ttl = struct.pack("!H", ttl)
        nseq = struct.pack("!I", nseq)
        src_ip = servent.ip.split(".")
        msg = type + ttl + nseq

        for i in range(0,4):
            msg += struct.pack("!b", int(src_ip[i]))

        src_port = struct.pack("!H", src_port)
        size = struct.pack("@H", len(info))
        msg += src_port + size + info.encode('ascii')

        return msg


    #+---- 2 ---+-- 4 -+--- 2 ---+---------------------------+ 
    #| TIPO = 9 | NSEQ | TAMANHO | VALOR (ate 400 carateres) | 
    #+----------+------+---------+---------------------------+
    def create_resp_msg(nseq, value):
        type = struct.pack("!H", 9)
        nseq = struct.pack("!I", nseq)
        size = struct.pack("@H", len(value))

        msg = type + nseq + size + value.encode('ascii')

        return msg

    # Tratamento das mensagens recebidas por um client vindas de um servent
    def receive_servent_msg(con, addr, nseq):
        msg_type = struct.unpack("!H", con.recv(2))[0]
        msg_nseq = struct.unpack("!I", con.recv(4))[0]

        (src_ip, src_port) = (addr[0], addr[1])

        # Tratamento em caso de erros na mensagem recebida
        if msg_type != 9 or msg_nseq != nseq:
            print("Mensagem incorreta recebida de " + str(src_ip) + ":" + str(src_port))
        else:
            msg_size = struct.unpack("@H", con.recv(2))[0]
            msg_value = con.recv(msg_size)
            print(msg_value.decode('ascii') + " " + str(src_ip) + ":" + str(src_port))

    # Obtem e retorna os dados da mensagem KEYREQ
    def get_keyreq_msg_data(con):
        nseq = struct.unpack("!I", con.recv(4))[0]
        size = struct.unpack("@H", con.recv(2))[0]
        key = con.recv(size)

        return nseq, key.decode('ascii')

    # Obtem e retorna os dados da mensagem TOPOREQ
    def get_toporeq_msg_data(con):
        nseq = struct.unpack("!I", con.recv(4))[0]

        return nseq

    # Obtem e retorna os dados da mensagem KEYFLOOD/TOPOFLOOD
    def get_flood_msg_data(con):
        ttl = struct.unpack("!H", con.recv(2))[0]
        nseq = struct.unpack("!I", con.recv(4))[0]

        src_ip_1 = struct.unpack("!b", con.recv(1))[0]
        src_ip_2 = struct.unpack("!b", con.recv(1))[0]
        src_ip_3 = struct.unpack("!b", con.recv(1))[0]
        src_ip_4 = struct.unpack("!b", con.recv(1))[0]

        src_ip = src_ip_1 + src_ip_2 + src_ip_3 + src_ip_4

        src_port = struct.unpack("!H", con.recv(2))[0]
        size = struct.unpack("@H", con.recv(2))[0]
        info = con.recv(size)

        return ttl, nseq, src_ip, src_port, info.decode('ascii')


    def send_msg_to_client(msg, src_ip, src_port):
        # Configura o socket pra enviar a resposta
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_addr = (src_ip, src_port)
        client_socket.connect(client_addr)
        client_socket.send(msg)
        client_socket.close()


    def flood_msg(servent, msg, connection):
        for input in inputs:
            # Envia a mensagem para todos vizinhos, exceto o que enviou a mensagem
            if input is not servent.servent_socket and input is not connection:
                input.send(msg)


    def verify_if_has_key(servent, key_values, key, nseq, port, connection, ttl):
        # Verifica se possui a chave consultada
        if key in key_values.keys():
            msg = Message.create_resp_msg(nseq, key_values[key])
            Message.send_msg_to_client(msg, servent.ip, servent.port)
        else:
            # Transmite a mensagem keyflood a todos os vizinhos, se TTL maior que 0
            if ttl > 0:
                msg = create_flood_message(servent, 7, 
                    ttl, nseq, port, key)
                Message.flood_msg(servent, msg, connection)


received_msgs = list() 		
connected_servents = list()	
connected_clients = {}		
outputs = [] 				
message_queues = {} 		

servent = Servent()  # Creates the servent object

inputs = [servent.servent_socket]	

while inputs:

	try:
		# Aguarda pelo menos um dos sockets estar pronto para ser processado
		readable, writable, exceptional = select.select(inputs, outputs, inputs)

		for current_socket in readable:
			if current_socket is servent.servent_socket:
				connection, client_address = current_socket.accept()
				connection.setblocking(0)
				inputs.append(connection)

				# Fornece a conexão para enfileirar os dados que desejamos enviar
				message_queues[connection] = queue.Queue()

			else:
				# Obtem o tipo da mensagem recebida
				msg_type = struct.unpack("!H", current_socket.recv(2))[0]

				if msg_type:
					# Trata o recebimento de mensagem do tipo ID
					if msg_type == 4:
						msg_port = struct.unpack("!H", current_socket.recv(2))[0]
						if msg_port == 0:
							connected_servents.append(current_socket.getpeername())
						else:
							connected_clients.update({ current_socket.getpeername() : msg_port })
					
					# Trata o recebimento de mensagem do tipo keyreq
					elif msg_type == 5:
						nseq, key = Message.get_keyreq_msg_data(current_socket)
						client_port = connected_clients[current_socket.getpeername()]
						Message.verify_if_has_key(servent, servent.key_values, key, nseq, client_port, current_socket, 3)
					
					# Trata o recebimento de mensagem do tipo toporeq
					elif msg_type == 6:
						nseq = Message.get_toporeq_msg_data(current_socket)
						info = servent.ip + ":" + str(servent.port)
						resp_msg = Message.create_resp_msg(nseq, info)

						client_port = connected_clients[current_socket.getpeername()]
						Message.send_msg_to_client(resp_msg, servent.ip, client_port)
						
						# Transmite a mensagem topoflood a todos os vizinhos
						msg = Message.create_flood_message(servent, 8, 
								3, nseq, client_port, info)
						Message.flood_msg(servent, msg, current_socket)
						
					# Trata o recebimento de mensagem do tipo keyflood
					elif msg_type == 7:
						ttl, nseq, src_ip, src_port, key = Message.get_flood_msg_data(current_socket)
						received_msg = (src_ip, src_port, nseq)

						# Verifica se ja recebeu essa mensagem antes
						if received_msg not in received_msgs:
							ttl -= 1
							received_msgs.append(received_msg)
							# Verifica se possui a chave consultada
							Message.verify_if_has_key(servent, servent.key_values, key, nseq, src_port, current_socket, ttl)
					
					# Trata o recebimento de mensagem do tipo topoflood
					elif msg_type == 8:
						ttl, nseq, src_ip, src_port, info = Message.get_flood_msg_data(current_socket)
						received_msg = (src_ip, src_port, nseq)
						# Verifica se ja recebeu essa mensagem antes
						if received_msg not in received_msgs:
							ttl -= 1
							received_msgs.append(received_msg)
							info += " " + servent.ip + ":" + str(servent.port)

							# Envia a mensagem resp para o client
							resp_msg = Message.create_resp_msg(nseq, info)
							Message.send_msg_to_client(resp_msg, servent.ip, src_port)

							if ttl > 0:
								# Transmite a mensagem a todos os vizinhos, exceto o que mandou a msg
								msg = Message.create_flood_message(servent, 8, 
									ttl, nseq, src_port, info)
								Message.flood_msg(servent, msg, current_socket)

					# Adiciona um canal de saida para resposta
					if current_socket not in outputs:
						outputs.append(current_socket)
				
				else:
					# Deixa de escutar por input na conexao
					if current_socket in outputs:
						outputs.remove(current_socket)
					inputs.remove(current_socket)
					current_socket.close()

					# Remove a fila de mensagem
					del message_queues[current_socket]

		# Gerencia saidas
		for current_socket in writable:
			try:
				next_msg = message_queues[current_socket].get_nowait()
			except queue.Empty:
				# Nenhuma mensagem aguardando, logo para de checkar
				outputs.remove(current_socket)
			else:
				current_socket.send(next_msg)

	except KeyboardInterrupt: # Encerra execucao no caso de Ctrl-C
		for current_socket in inputs:
			current_socket.close()
		servent.servent_socket.close()
		sys.exit()