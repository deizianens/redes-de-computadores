'''
Receberá do usuário as chaves que devem ser consultadas 
e exibirá os resultados que forem recebidos para as consultas.
'''
import sys
import socket
import struct

class Client: # Class to represent each client
    def __init__(self):
        self.port = sys.argv[1]
        self.ipPort = sys.argv[2]
        self.serventIp, self.serventPort = sys.argv[2].split(':') # Gets the servent ip and port from the command line argument
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
        consult = message[2:]
        msg = struct.pack('!H', 5) + struct.pack('!I', client.seqNum) + struct.pack('@H', len(consult)) 
        msg += consult.encode('ascii')

        client.sockets[client.ipPort].send(msg)
        client.seqNum += 1

        while 1:
            try:
                client.sockets['0'].settimeout(4)
                # client.sockets['0'].listen()
                conn, client_address = client.sockets['0'].accept()
                client.sockets[client_address] = conn
                Message.received_messages(conn, client_address, client.seqNum)

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
            msg = struct.pack('!H', 6) + struct.pack('!I', client.seqNum)
            client.sockets[client.ipPort].send(msg)
            client.seqNum += 1

            while 1:
                try:
                    client.sockets['0'].settimeout(4)
                    # client.sockets['0'].listen()
                    conn, client_address = client.sockets['0'].accept()
                    client.sockets[client_address] = conn
                    Message.received_messages(conn, client_address, client.seqNum)

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

while 1:
    message = input('Insira um comando:\n> ')

    if message[0].upper() == '?':
        message = message[1:].replace(' ','').replace('\t','') # Replaces the spaces and tabs
        Message.sendKeyReq(client, message)

    elif message[0].upper() == 'T':
        Message.sendTopoReq(client)

    elif message[0].upper() == 'Q':
        for con in client.sockets:
                client.sockets[con].close() 
        print('Socket do client finalizado com sucesso.')
        break

    else:
        print('Comando invalido. Por favor, insira um novo comando.\n')

    print('')