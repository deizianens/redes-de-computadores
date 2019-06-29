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
        self.createSockets()

    def createSockets(self):
        try:
            self.client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP socket creation
            self.client_sock.bind(("", int(self.port)))
            # self.client_sock.listen()

        except socket.error as e:
            print("Erro de conexão (1). ", e)
            sys.exit()

        try:
            self.servent_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP socket creation
            self.servent_sock.connect((self.serventIp, self.serventPort))
            
            '''
            ID
            +---- 2 ---+--- 2 ---------------------------+
            | TIPO = 4 | PORTO (ou zero se for servent) |
            +----------+---------------------------------+
            '''    
            msg = struct.pack('!H', 4) + struct.pack('!H', int(self.port))   # ID message to identify as servent or client (servent = 0, client = port)
            self.servent_sock.send(msg)

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
        consult = message
        msg = struct.pack('!H', 5) + struct.pack('!I', client.seqNum) + struct.pack('@H', len(consult)) 
        msg += consult.encode('ascii')

        client.servent_sock.send(msg)
        client.seqNum += 1
        
        while 1:
            try:
                client.client_sock.settimeout(4)
                client.client_sock.listen()
                conn, client_address = client.client_sock.accept()
                ans = Message.received_messages(conn, client.seqNum)

            except socket.timeout: # If timeout occurs
                if not ans:
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
            client.servent_sock.send(msg)
            client.seqNum += 1            
            
            while 1:
                try:
                    client.client_sock.settimeout(4)
                    client.client_sock.listen()
                    conn, client_address = client.client_sock.accept()
                    ans = Message.received_messages(conn, client.seqNum)

                except socket.timeout: # If timeout occurs
                    if not ans:
                        print('Nenhuma resposta recebida.')
                    return


    def received_messages(conn, nseq):
        msg = conn.recv(2)
        if msg:
            recv_msg = struct.unpack("!H", msg)
            msg_type = recv_msg[0]

            if msg_type == 9:  # client only receives RESP messages
                msg_nseq = struct.unpack("!I", conn.recv(4))[0]
                msg_size = struct.unpack("@H", conn.recv(2))[0]
                msg_value = conn.recv(msg_size)
                (src_ip, src_port) = conn.getpeername()

                if(msg_nseq == nseq):
                    print(msg_value.decode('ascii') + " " + str(src_ip) + ":" + str(src_port))
                    return True
                else:
                    print("Mensagem incorreta recebida de "+str(src_ip)+":"+str(src_port))
                    return False
            else:
                (src_ip, src_port) = conn.getpeername()
                print("Mensagem incorreta recebida de "+str(src_ip)+":"+str(src_port))
        return False
           


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
