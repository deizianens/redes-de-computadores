'''
Receberá do usuário as chaves que devem ser consultadas 
e exibirá os resultados que forem recebidos para as consultas.
'''
import sys
import socket
import struct
import select

class Client: # Class to represent each client
    def __init__(self):
        self.port = sys.argv[1]
        self.ipPort = sys.argv[2]
        self.serventIp, self.serventPort = sys.argv[2].split(':') # Gets the servent ip and port from the input_ line argument
        self.serventPort = int(self.serventPort) # Casts the port to be a int
        self.seqNum = 0 
        self.sockets = {}
        self.sockets['stdin'] = sys.stdin

    def createSockets(self):
        try:
            client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP socket creation
            client_sock.bind(("", int(self.port)))
            client_sock.listen()

            self.sockets['0'] = client_sock
        except socket.error as e:
            print("Erro de conexão (1). ", e)
            sys.exit()

        try:
            servent_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP socket creation
            servent_sock.connect((self.serventIp, self.serventPort))
            
            '''
            ID
            +---- 2 ---+--- 2 ---------------------------+
            | TIPO = 4 | PORTO (ou zero se for servent) |
            +----------+---------------------------------+
            '''    
            msg = struct.pack('!H', 4) + struct.pack('!H', int(self.port))   # ID message to identify as servent or client (servent = 0, client = port)
            servent_sock.send(msg)

            self.sockets[self.ipPort]  = servent_sock

        except socket.error as e:
            print("Erro de conexão (2). ", e)
            sys.exit(1)

class Message: # Class to represent the client message methods
    '''
    +---- 2 ---+-- 4 -+--- 2 ---+----------\\---------------+
    | TIPO = 5 | NSEQ | TAMANHO | CHAVE (up to 400 carateres) |
    +----------+------+---------+----------\\---------------+
    '''
    def sendKeyReq(client, message): # Method to send a keyReq message to a servent
        client.seqNum += 1
        consult = message
        msg = struct.pack('!H', 5) + struct.pack('!I', client.seqNum) + struct.pack('@H', len(consult)) 
        msg += consult.encode('ascii')

        client.sockets[client.ipPort].send(msg)

        # while 1:
        try:
                client.sockets['0'].settimeout(4)
                # client.sockets['0'].listen()
                conn, client_address = client.sockets['0'].accept()
                client.sockets[client_address] = conn
                # Message.received_messages(conn, client_address, client.seqNum)

        except socket.timeout: # If timeout occurs
                print('Nenhuma resposta recebida.')
                return
                
    '''
    TOPOREQ
    +---- 2 ---+-- 4 -+
    | TIPO = 6 | NSEQ |
    +----------+------+
    '''
    def sendTopoReq(client): # Method to send a topoReq message to a servent
            client.seqNum += 1            
            msg = struct.pack('!H', 6) + struct.pack('!I', client.seqNum)
            client.sockets[client.ipPort].send(msg)
            
            # while 1:
            try:
                    client.sockets['0'].settimeout(4)
                    # client.sockets['0'].listen()
                    conn, client_address = client.sockets['0'].accept()
                    client.sockets[client_address] = conn
                    # Message.received_messages(conn, client_address, client.seqNum)

            except socket.timeout: # If timeout occurs
                    print('Nenhuma resposta recebida.')
                    return

    def received_messages(conn, addr, nseq):
        msg_type = struct.unpack("!H", conn.recv(2))[0]
        msg_nseq = struct.unpack("!I", conn.recv(4))[0]

        (src_ip, src_port) = (addr[0], addr[1])

        msg_size = struct.unpack("@H", conn.recv(2))[0]
        msg_value = conn.recv(msg_size)
        print(msg_value.decode('ascii') + " " + str(src_ip) + ":" + str(src_port))


client = Client() # Creates the object to represent the client
client.createSockets() # sockets to comunicate

print('SERVENT IP:', client.serventIp, '\nSERVENT PORT:', client.serventPort)

try:
    while(1):
        read_s, write_s, except_s = select.select([client.sockets[sock] for sock in client.sockets], [], [])

        for current_socket in read_s:
                if current_socket is client.sockets['stdin']:
                        input_ = current_socket.readline().replace('\0', "").replace('\n', "")

                        if ((input_[0] == "?" and (input_[1] == " " or input_[1] == '\t')) or (input_ == "T" or input_ == 't')):

                            if(input_[0] == "?" and (input_[1] == " " or input_[1] == '\t')):
                                key_ = input_[2:]
                                message= struct.pack('>h', 5) + struct.pack('>i', client.seqNum) + struct.pack('>h', len(key_)) 
                                message+= str.encode(key_)

                            if(input_ == "T" or input_ == 't'):
                                message= struct.pack('>h', 6) + struct.pack('>i', client.seqNum)

                            client.sockets[client.ipPort].send(message)

                            try:
                                client.sockets['0'].settimeout(4)
                                connection, client_address = client.sockets['0'].accept()
                                client.sockets[client_address] = connection
                                
                            except socket.timeout:
                                print("Nenhuma resposta recebida")     

                        elif(input_ == "Q" or input_ == 'q'):
                            raise KeyboardInterrupt
                        else:
                            print("Comando desconhecido")

                elif current_socket is client.sockets['0']:
                        try:
                            connection, client_address = current_socket.accept()
                            client.sockets[client_address] = connection
                        except socket.timeout:
                            continue
                
                else:
                        #  RESP
                        #+---- 2 ---+-- 4 -+--- 2 ---+----------\\---------------+
                        #| TIPO = 9 | NSEQ | TAMANHO | VALOR (até 400 carateres) |
                        #+----------+------+---------+----------\\---------------+
                        data = current_socket.recv(2)  # receive message type
                        
                        if data:
                            type_ = struct.unpack('>h', data)[0]
                            if type_ == 9:
                                nseq = struct.unpack('>i', current_socket.recv(4))[0]
                                if(nseq != client.seqNum):
                                    print("Mensagem incorreta.")
                                else:
                                    size = struct.unpack('>h', current_socket.recv(2))[0]

                                    value = ""
                                    for _ in range(size):
                                        value += bytes.decode(current_socket.recv(1))

                                    print(value, str(current_socket.getpeername()[0])+":"+str(current_socket.getpeername()[1]))

                                del client.sockets[current_socket.getpeername()]
                                current_socket.close()
                        else:
                            raise KeyboardInterrupt
except KeyboardInterrupt:
    raise KeyboardInterrupt
except Exception as e:
    print(e)
    raise
