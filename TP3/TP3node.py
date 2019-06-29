'''
Responsável pelo armazenamento da base de dados chave-valor 
e pelo controle da troca de mensagens com seus parceiros
'''
import sys
import socket
import struct
import select

class Servent:  # Class to represent each servent
    # ./TP3node <porto-local> <banco-chave-valor> [ip1:porto1 [ip2:porto2 ...]]
    def __init__(self):
        self.ip = '127.0.0.1'  # Local host IP
        self.port = int(sys.argv[1])
        self.sockets = {}
        self.neighborsPort = {}
        # List to store the messages received by each servent
        self.receivedMessagesList = []
        # Dictionary of keys given by the input file
        self.keyDictionary = {}  
        self.keyDictionaryConstructor(sys.argv[2])
        # Local port received from command line argument
        self.serventListConstructor(sys.argv[3:])
        self.createSocket() # create servent socket


    def createSocket(self):
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP socket creation
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.setblocking(0) # no timeout   
            server_socket.bind((self.ip, int(self.port)))
            server_socket.listen()

            self.sockets['0'] = server_socket
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except socket.error as e:
            print(e)
            raise KeyboardInterrupt


    # Method to construct the key dictionary from the input file
    def keyDictionaryConstructor(self, inputFile):
        file = open(inputFile, 'r')
        keys = file.readlines()

        for key in keys:
            # If the first character from the line isn't a comment (#)
            if key[0] != '#':
                key = key.split()
                # Save the key and the value in the key Dictionary
                self.keyDictionary[key[0]] = str.join(' ', (key[1:]))
                # print(self.keyDictionary)
      

    # Method to construct the servent list (connect to neighbor)
    def serventListConstructor(self, servents):
        for addr in set(servents):
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                conn.connect((addr.split(':')[0] , int(addr.split(':')[1]))) 
                conn.setblocking(0)

                # send id message to conect                                
                id_msg = struct.pack('!H', 4) + struct.pack('!H', 0)   
                conn.send(id_msg)

                self.sockets[(addr.split(":")[0] , int(addr.split(":")[1]))] = conn
                self.neighborsPort[(addr.split(":")[0] , int(addr.split(":")[1]))] = 0

            except ConnectionRefusedError:
                print("Erro de conexão " , addr)


    # Method to check if the received message is new in the servent by looking into the receivedMessagesList
    def checkMessageIsNew(self, recvMsg):
        if recvMsg in self.receivedMessagesList:
                return False

        # If the message is new, insert the message in the receivedMessagesList
        self.receivedMessagesList.append(recvMsg)
        return True


class Message:  # Class to represent the servent message methods
    '''
    +---- 2 ------+- 2 -+-- 4 -+--- 4 ---+----- 2 ----+--- 2 ---+----------\\--------------+
    | TIPO = 7, 8 | TTL | NSEQ | IP_ORIG | PORTO_ORIG | TAMANHO | INFO (at´e 400 carateres) |
    +-------------+-----+------+---------+------------+---------+----------\\--------------+

    '''
    def recvKeyReq(servent, key, num_seq, porto_orig, current_socket):  # Method to deal with keyReq messages
        # If this servent has the key in his keyDictionary, send a resp to the client
        if key in servent.keyDictionary.keys():
            print("Servent possui a chave. Enviando resposta para cliente no porto "+str(porto_orig))
            Message.sendResp(servent, num_seq, servent.keyDictionary[key], servent.ip, porto_orig)
        else:
            print("Servent não possui a chave. Iniciando alagamento.")
            keyFloodMsg = struct.pack("!H", 7)  # Message type
            keyFloodMsg += struct.pack("!H", 3)  # TTL
            keyFloodMsg += struct.pack("!I", num_seq)  # Sequence Number

            src_ip = servent.ip.split(".")
            for i in range(0,4):
                keyFloodMsg += struct.pack("!b", int(src_ip[i]))

            keyFloodMsg += struct.pack("!H", porto_orig)  # Client port
            keyFloodMsg += struct.pack("@H", len(key)) # message size
            keyFloodMsg += key.encode('ascii')

            Message.sendMessageToServentList(servent, keyFloodMsg, current_socket)


    def recvTopoReq(servent, num_seq, porto_orig, current_socket):  # Method to deal with topoReq messages
        info = servent.ip + ":" + str(servent.port)        
        Message.sendResp(servent, num_seq, info, servent.ip, servent.neighborsPort[current_socket.getpeername()])
        
        topoFloodMsg = struct.pack("!H", 8)  # Message type
        topoFloodMsg += struct.pack("!H", 3)  # TTL
        topoFloodMsg += struct.pack("!I", num_seq)  # Sequence Number

        src_ip = servent.ip.split(".")
        for i in range(0,4):
            topoFloodMsg += struct.pack("!b", int(src_ip[i]))
        
        topoFloodMsg += struct.pack("!H", porto_orig)  # Client port
        topoFloodMsg += struct.pack("@H", len(info)) # message size
        topoFloodMsg += info.encode('ascii')

        Message.sendMessageToServentList(servent, topoFloodMsg, current_socket)


    def recvKeyFlood(servent, ttl, num_seq, ip_orig, porto_orig, size, info, current_socket):  # Method to deal with keyFlood messages
        if servent.checkMessageIsNew((ip_orig, porto_orig, num_seq)):  # If the key is in the keyDictionary
            if info in servent.keyDictionary.keys():
                Message.sendResp(servent, num_seq, servent.keyDictionary[key], servent.ip, porto_orig)
            else:
                ttl -= 1
                keyFloodMsg = struct.pack("!H", 7)  # Message type
                keyFloodMsg += struct.pack("!H", ttl)  # TTL
                keyFloodMsg += struct.pack("!I", num_seq)  # Sequence Number

                src_ip = servent.ip.split(".")
                for i in range(0,4):
                    keyFloodMsg += struct.pack("!b", int(src_ip[i]))

                keyFloodMsg += struct.pack("!H", porto_orig) # Client port
                keyFloodMsg += struct.pack("@H", size) # message size
                keyFloodMsg += info.encode('ascii')

                # if valid TTL, continue, else discard
                if(ttl > 0):
                    Message.sendMessageToServentList(servent, keyFloodMsg, current_socket)


    def recvTopoFlood(servent, ttl, num_seq, ip_orig, porto_orig, size, info, current_socket):  # Method to deal with topoFlood messages
        if servent.checkMessageIsNew((ip_orig, porto_orig, num_seq)):  # If the key is in the keyDictionary
            if info in servent.keyDictionary.keys():
                Message.sendResp(servent, num_seq, servent.keyDictionary[key], servent.ip, porto_orig)
            else:
                ttl -= 1
                topoFloodMsg = struct.pack("!H", 8)  # Message type
                topoFloodMsg += struct.pack("!H", ttl)  # TTL
                topoFloodMsg += struct.pack("!I", num_seq)  # Sequence Number

                src_ip = servent.ip.split(".")
                for i in range(0,4):
                    topoFloodMsg += struct.pack("!b", int(src_ip[i]))

                topoFloodMsg += struct.pack("!H", porto_orig) # Client port
                topoFloodMsg += struct.pack("@H", size) # message size
                info = " " + servent.ip + ":" + str(servent.port)
                topoFloodMsg += info.encode('ascii')

                # if valid TTL, continue, else discard
                if(ttl > 0):
                    Message.sendMessageToServentList(servent, topoFloodMsg, current_socket)


    '''
    RESP
    +---- 2 ---+-- 4 -+--- 2 ---+----------\\---------------+
    | TIPO = 9 | NSEQ | TAMANHO | VALOR (up to 400 characters) |
    +----------+------+---------+----------\\---------------+
    '''
    # Method to send the resp message to the client from a keyReq
    def sendResp(servent, nseq, value, ip, port):
        newMessage = struct.pack("!H", 9)  # Message type
        newMessage += struct.pack("!I", nseq)  # Sequence Number
        newMessage += struct.pack("@H", len(value))  # Message size
        newMessage += value.encode('ascii')
        try:
            s = socket.socket(socket.AF_INET , socket.SOCK_STREAM)
            s.connect((ip, port))
            s.send(newMessage)
            s.close()
            #print("Dado enviado: " , data)
        except socket.error as e:
            print("Falha ao enviar na porta recebida." , (ip, port) , e )

    # Method to send the message to all servents in the servent list
    def sendMessageToServentList(servent, message, current_socket):
        for neighbor in servent.sockets:
            if neighbor == '0': # dont send to servent or who sent me
                continue

            if servent.neighborsPort[neighbor] == 0 and neighbor != current_socket.getpeername():
                print("Enviando mensagem de alagamento para "+str(servent.sockets[neighbor].getpeername()))
                servent.sockets[neighbor].send(message)
                

    # Method to construct the client address to auxiliate the resp message methods
    def clientAddressConstructor(message):
        clientPort = int.from_bytes(message[12:14], 'big')

        return ('127.0.0.1', clientPort)


    def TTLIsValid(message):  # Method to verify the TTL value
        return True if int.from_bytes(message[2:4], 'big') > 0 else False


servent = Servent()  # Creates the servent object

while (servent.sockets):
    try:
        
        read_s, write_s, except_s = select.select([servent.sockets[sock] for sock in servent.sockets], [], [])

        for current_socket in read_s:
            
            if current_socket is servent.sockets['0']: # servent socket 
                conn, client_address = current_socket.accept()
                conn.setblocking(0) # No timeouts.
                servent.sockets[client_address] = conn

            else: # identify what kind of message is coming
                recv_msg = struct.unpack('!H', current_socket.recv(2))[0] 
                if (recv_msg):
                    '''
                    ID  
                    +---- 2 ---+--- 2 ---------------------------+
                    | TIPO = 4 | PORTO (ou zero se for servent) |
                    +----------+---------------------------------+
                    '''
                    if (recv_msg == 4): #ID message
                        print("Recebeu ID em "+str(current_socket.getpeername()))
                        recv_port = struct.unpack("!H", current_socket.recv(2))[0]
                        servent.neighborsPort[current_socket.getpeername()] = recv_port
                
                    elif (recv_msg == 5): # KEYREQ
                        '''
                        KEYREQ
                        +---- 2 ---+-- 4 -+--- 2 ---+----------\\---------------+
                        | TIPO = 5 | NSEQ | TAMANHO | CHAVE (até 400 carateres) |
                        +----------+------+---------+----------\\---------------+
                        '''
                        num_seq = struct.unpack("!I", current_socket.recv(4))[0]
                        size = struct.unpack("!H", current_socket.recv(2))[0]
                        key = current_socket.recv(size).decode('ascii')

                        Message.recvKeyReq(servent, key, num_seq, servent.neighborsPort[current_socket.getpeername()], current_socket)

                    elif (recv_msg == 6): #TOPOREQ
                        '''
                        +---- 2 ---+-- 4 -+
                        | TIPO = 6 | NSEQ |
                        +----------+------+
                        '''
                        num_seq = struct.unpack("!I", current_socket.recv(4))[0]
                        
                        Message.recvTopoReq(servent, num_seq, servent.neighborsPort[current_socket.getpeername()], current_socket)

                    elif (recv_msg == 7): #KEYFLOOD OR TOPOFLOOD
                        '''
                        +---- 2 ------+- 2 -+-- 4 -+--- 4 ---+----- 2 ----+--- 2 ---+----------\\--------------+
                        | TIPO = 7, 8 | TTL | NSEQ | IP_ORIG | PORTO_ORIG | TAMANHO | INFO (at´e 400 carateres) |
                        +-------------+-----+------+---------+------------+---------+----------\\--------------+
                        '''
                        ttl = struct.unpack('!H', current_socket.recv(2))[0]        
                        nseq = struct.unpack('!I', current_socket.recv(4))[0] 

                        ip1 = struct.unpack("!b", current_socket.recv(1))[0]
                        ip2 = struct.unpack("!b", current_socket.recv(1))[0]
                        ip3 = struct.unpack("!b", current_socket.recv(1))[0]
                        ip4 = struct.unpack("!b", current_socket.recv(1))[0] 
                        ip_orig = ip1 + ip2 + ip3 + ip4

                        porto_orig = struct.unpack('!H', current_socket.recv(2))[0] 
                        size = struct.unpack('!H', current_socket.recv(2))[0]    
                        info = current_socket.recv(size).decode('ascii')

                        Message.recvKeyFlood(servent, ttl, nseq, ip_orig, porto_orig, size, info, current_socket)

                    elif (recv_msg == 8): #KEYFLOOD OR TOPOFLOOD
                        ttl = struct.unpack('!H', current_socket.recv(2))[0]        
                        nseq = struct.unpack('!I', current_socket.recv(4))[0] 

                        ip1 = struct.unpack("!b", current_socket.recv(1))[0]
                        ip2 = struct.unpack("!b", current_socket.recv(1))[0]
                        ip3 = struct.unpack("!b", current_socket.recv(1))[0]
                        ip4 = struct.unpack("!b", current_socket.recv(1))[0] 
                        ip_orig = ip1 + ip2 + ip3 + ip4

                        porto_orig = struct.unpack('!H', current_socket.recv(2))[0] 
                        size = struct.unpack('!H', current_socket.recv(2))[0]    
                        info = current_socket.recv(size).decode('ascii')

                        Message.recvTopoFlood(servent, ttl, nseq, ip_orig, porto_orig, size, info, current_socket)
                else:
                    del servent.sockets[current_socket.getpeername()]
                    current_socket.close()

    except KeyboardInterrupt:
        raise KeyboardInterrupt