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
     # Method to construct the key dictionary from the input file
    def keyDictionaryConstructor(self, inputFile):
        try:
            file = open(inputFile, "r")
        except (OSError, IOError) as error:
            print("Erro ao abrir arquivo.")

        dictionary = {}
        for line in file:
            if not line.isspace(): 
                words = line.split()
                if words[0] != '#': # If the first character from the line isn't a comment (#)
                    first_character = str.strip(words[0][0])
                    if first_character != '#': 
                        key = str.strip(words[0])
                        text = words[1:]
                        value = ' '.join(text)
                        dictionary.update({ key : value }) # Save the key and the value in the key Dictionary

        file.close()
        return dictionary
    

    def createSocket(self, servert_addr):
        # TCP socket creation
        self.servent_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.servent_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.servent_socket.setblocking(0)
        self.servent_socket.bind(servert_addr)

        return self.servent_socket


    # Method to construct the servent list
    def connectNeighbors(self, connection_socket, neighbor):
        neighbor_ip = neighbor.split(":")[0]
        neighbor_port = int(neighbor.split(":")[1])
        neighbor_addr = (neighbor_ip, neighbor_port)

        connection_socket.connect(neighbor_addr)
        connection_socket.setblocking(0)

        # send id message to conect
        msg = Message.createID(0)
        connection_socket.send(msg)


class Message:
    #+---- 2 ---+--- 2 ---------------------------+
    #| TIPO = 4 |  PORTO (ou zero se for servent) |
    #+----------+---------------------------------+
    def createID(port):
        type = struct.pack("!H", 4)
        port = struct.pack("!H", port)

        msg = type + port

        return msg


    #+---- 2 ------+- 2 -+-- 4 -+--- 4 ---+----- 2 ----+--- 2 ---+--------------------------+ 
    #| TIPO = 7, 8 | TTL | NSEQ | IP_ORIG | PORTO_ORIG | TAMANHO | INFO (ate 400 carateres) | 
    #+-------------+-----+------+---------+------------+---------+--------------------------+
    def createFLOOD(servent, msg_type, ttl, nseq, src_port, info):
        
        if msg_type == 7:
            type = struct.pack("!H", 7)
        else:
            type = struct.pack("!H", 8)

        ttl = struct.pack("!H", ttl)
        nseq = struct.pack("!I", nseq)
        src_ip = ip.split(".")
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
    def createRESP(nseq, value):
        type = struct.pack("!H", 9)
        nseq = struct.pack("!I", nseq)
        size = struct.pack("@H", len(value))

        msg = type + nseq + size + value.encode('ascii')

        return msg


    # Method to deal with keyReq messages
    def getKEYREQ(con):
        nseq = struct.unpack("!I", con.recv(4))[0]
        size = struct.unpack("@H", con.recv(2))[0]
        key = con.recv(size)

        return nseq, key.decode('ascii')

    # Method to deal with topoReq messages
    def getTOPOREQ(con):
        nseq = struct.unpack("!I", con.recv(4))[0]

        return nseq

    # Method to deal with (key/topo)Flood messages
    def getFLOOD(con):
        ttl = struct.unpack("!H", con.recv(2))[0]
        nseq = struct.unpack("!I", con.recv(4))[0]

        ip_1 = struct.unpack("!b", con.recv(1))[0]
        ip_2 = struct.unpack("!b", con.recv(1))[0]
        ip_3 = struct.unpack("!b", con.recv(1))[0]
        ip_4 = struct.unpack("!b", con.recv(1))[0]

        src_ip = ip_1 + ip_2 + ip_3 + ip_4

        src_port = struct.unpack("!H", con.recv(2))[0]
        size = struct.unpack("@H", con.recv(2))[0]
        info = con.recv(size)

        return ttl, nseq, src_ip, src_port, info.decode('ascii')

    #  Method to send the resp message to the client
    def sendMessageToClient(msg, src_ip, src_port):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_addr = (src_ip, src_port)
        client_socket.connect(client_addr)
        client_socket.send(msg)
        client_socket.close()

    #  Method to send the message to all servents in the servent list
    def flooding(servent, msg, connection):
        for input in inputs:
            # dont send to servent or who sent me
            if input is not servent.servent_socket and input is not connection:
                input.send(msg)


    # Method to check received messages
    def checkKey(servent, key_values, key, nseq, port, connection, ttl):
         # If this servent has the key in his keyDictionary, send a resp to the client
        if key in key_values.keys():
            msg = Message.createRESP(nseq, key_values[key])
            Message.sendMessageToClient(msg, ip, port)
        else:
            if ttl > 0:
                msg = createFLOOD(servent, 7, 
                    ttl, nseq, port, key)
                Message.flooding(servent, msg, connection)


servent = Servent()  # Creates the servent object

params = len(sys.argv)
ip = '127.0.0.1'  # Local host IP
port = int(sys.argv[1])
file = sys.argv[2]

neighbors = list()
for i in range(3, params):
    neighbors.append(sys.argv[i])

key_values = {}
key_values = servent.keyDictionaryConstructor(file)

# main socket
servent_addr = (ip, port)
servent.servent_socket = servent.createSocket(servent_addr)
servent.servent_socket.listen()

received_msgs = list() 		
connected_servents = list()	
connected_clients = {}		
inputs = [servent.servent_socket]	
outputs = [] 				
message_queues = {} 		

for neighbor in neighbors:
    connection_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servent.connectNeighbors(connection_socket, neighbor)
    inputs.append(connection_socket)
    message_queues[connection_socket] = queue.Queue()

while inputs:

    try:
        readable, writable, exceptional = select.select(inputs, outputs, inputs)

        for current_socket in readable:
            if current_socket is servent.servent_socket: # servent socket = new connection
                connection, client_address = current_socket.accept()
                connection.setblocking(0)
                inputs.append(connection)

                message_queues[connection] = queue.Queue()

            else:
                # identify what kind of message is coming
                msg_type = struct.unpack("!H", current_socket.recv(2))[0]

                if msg_type:
                    '''
                    ID  
                    +---- 2 ---+--- 2 ---------------------------+
                    | TIPO = 4 | PORTO (ou zero se for servent) |
                    +----------+---------------------------------+
                    '''
                    if msg_type == 4:
                        msg_port = struct.unpack("!H", current_socket.recv(2))[0]
                        if msg_port == 0:
                            connected_servents.append(current_socket.getpeername())
                        else:
                            connected_clients.update({ current_socket.getpeername() : msg_port })
                
                    elif msg_type == 5:
                        '''
                        KEYREQ
                        +---- 2 ---+-- 4 -+--- 2 ---+----------\\---------------+
                        | TIPO = 5 | NSEQ | TAMANHO | CHAVE (até 400 carateres) |
                        +----------+------+---------+----------\\---------------+
                        '''
                        nseq, key = Message.getKEYREQ(current_socket)
                        client_port = connected_clients[current_socket.getpeername()]
                        Message.checkKey(servent, key_values, key, nseq, client_port, current_socket, 3)
                    
                    elif msg_type == 6:
                        '''
                        +---- 2 ---+-- 4 -+
                        | TIPO = 6 | NSEQ |
                        +----------+------+
                        '''
                        nseq = Message.getTOPOREQ(current_socket)
                        info = ip + ":" + str(port)
                        resp_msg = Message.createRESP(nseq, info)

                        client_port = connected_clients[current_socket.getpeername()]
                        Message.sendMessageToClient(resp_msg, ip, client_port)
                        
                        msg = Message.createFLOOD(servent, 8, 
                                3, nseq, client_port, info)
                        Message.flooding(servent, msg, current_socket)
                        
                    elif msg_type == 7:
                        '''
                        +---- 2 ------+- 2 -+-- 4 -+--- 4 ---+----- 2 ----+--- 2 ---+----------\\--------------+
                        | TIPO = 7, 8 | TTL | NSEQ | IP_ORIG | PORTO_ORIG | TAMANHO | INFO (ate 400 carateres) |
                        +-------------+-----+------+---------+------------+---------+----------\\--------------+
                        '''
                        ttl, nseq, src_ip, src_port, key = Message.getFLOOD(current_socket)
                        received_msg = (src_ip, src_port, nseq)

                        # check if the received message is new in the servent 
                        if received_msg not in received_msgs:
                            ttl -= 1
                            received_msgs.append(received_msg)
                           
                            Message.checkKey(servent, key_values, key, nseq, src_port, current_socket, ttl)
                    
                    elif msg_type == 8:
                        '''
                        +---- 2 ------+- 2 -+-- 4 -+--- 4 ---+----- 2 ----+--- 2 ---+----------\\--------------+
                        | TIPO = 7, 8 | TTL | NSEQ | IP_ORIG | PORTO_ORIG | TAMANHO | INFO (ate 400 carateres) |
                        +-------------+-----+------+---------+------------+---------+----------\\--------------+
                        '''
                        ttl, nseq, src_ip, src_port, info = Message.getFLOOD(current_socket)
                        received_msg = (src_ip, src_port, nseq)
                        # check if the received message is new in the servent 
                        if received_msg not in received_msgs:
                            ttl -= 1
                            received_msgs.append(received_msg)
                            info += " " + ip + ":" + str(port)

                            # answer to client
                            resp_msg = Message.createRESP(nseq, info)
                            Message.sendMessageToClient(resp_msg, ip, src_port)

                            if ttl > 0:
                                msg = Message.createFLOOD(servent, 8, 
                                    ttl, nseq, src_port, info)
                                Message.flooding(servent, msg, current_socket)

                    if current_socket not in outputs:
                        outputs.append(current_socket)
                
                else:
                    # remove connection
                    if current_socket in outputs:
                        outputs.remove(current_socket)
                    inputs.remove(current_socket)
                    current_socket.close()

                    del message_queues[current_socket]

        for current_socket in writable:
            try:
                next_msg = message_queues[current_socket].get_nowait()
            except queue.Empty:
                #No message
                outputs.remove(current_socket)
            else:
                current_socket.send(next_msg)

    except KeyboardInterrupt: 
        for current_socket in inputs:
            current_socket.close()
        servent.servent_socket.close()
        sys.exit()