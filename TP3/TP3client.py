'''
Receberá do usuário as chaves que devem ser consultadas 
e exibirá os resultados que forem recebidos para as consultas.
'''
import sys
import socket
import struct

class Client: # Class to represent each client
    def __init__(self):
        self.port = int(sys.argv[1])
        self.serventIp, self.serventPort = sys.argv[2].split(':') # Gets the servent ip and port from the command line argument
        self.serventPort = int(self.serventPort) # Casts the port to be a int
        self.seqNum = 0 
        self.sockets = {}
        self.sockets['stdin'] = sys.stdin
        

    def createSockets(self):
        try:
            client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP socket creation
            client_sock.bind(("", self.port))
            client_sock.listen()

            self.sockets['0'] = client_sock
        except:
            print("Erro de conexão (1).")
            sys.exit()

        try:
            servent_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP socket creation
            servent_sock.connect(self.serventIp, self.serventPort)
            servent_sock.listen()

            self.sockets['0'] = servent_sock
            '''
            ID
            +---- 2 ---+--- 2 ---------------------------+
            | TIPO = 4 | PORTO (ou zero se for servent) |
            +----------+---------------------------------+
            '''
            msg = struct.pack('>h', 4) + struct.pack('>h', int(self.port))   # ID message to identify as servent or client (servent = 0, client = port)
            servent_sock.send(msg)
            self.sockets[self.serventIp]  = servent_sock

        except:
            print("Erro de conexão (2).")
            sys.exit()

class Message: # Class to represent the client message methods
    '''
    +---- 2 ---+-- 4 -+--- 2 ---+----------\\---------------+
    | TIPO = 5 | NSEQ | TAMANHO | CHAVE (up to 400 carateres) |
    +----------+------+---------+----------\\---------------+
    '''
    def sendKeyReq(client, message): # Method to send a keyReq message to a servent
        consult = message[2:]
        msg = struct.pack('>h', 5) + struct.pack('>i', client.seqNum) + struct.pack('>h', len(consult)) 
        msg += str.encode(consult)

        client.sock.send(msg)
        client.seqNum += 1

        responses = [] # List to store the responses
        while 1:
            try:
                client.sock.settimeout(4) # 4 seconds to respond

                responses.append(client.sock.recvfrom(408)) # 2 (message type size) + 4 (sequence number size) + 2 (message size) + 400 (info or key size)

            except socket.timeout: # If the first timeout occurs
                if len(responses) == 0: # And none response was received, try again
                    consult = message[2:]
                    msg = struct.pack('>h', 5) + struct.pack('>i', client.seqNum) + struct.pack('>h', len(consult)) 
                    msg += str.encode(consult)

                    client.sock.send(msg)
                    client.seqNum += 1

                    while 1:
                        try:
                            client.sock.settimeout(4)

                            responses.append(client.sock.recvfrom(406)) # 2 (message type size) + 4 (sequence number size) + 400 (info or key size)

                        except socket.timeout: # If the second timeout occurs
                            if len(responses) == 0: # And none response was received
                                print('Nenhuma resposta recebida.')
                                return

                            else:
                                Message.printResponses(struct.pack('>i', client.seqNum-1), responses) # If any response was received, print those
                                return
                else:
                    Message.printResponses(struct.pack('>i', client.seqNum-1), responses) # If any response was received, print those
                    return

    '''
    TOPOREQ
    +---- 2 ---+-- 4 -+
    | TIPO = 6 | NSEQ |
    +----------+------+
    '''
    def sendTopoReq(client): # Method to send a topoReq message to a servent
            msg = struct.pack('>h', 6) + struct.pack('>i', client.seqNum)
            client.sock.send(msg)
            client.seqNum += 1

            responses = [] # List to store the responses
            while 1:
                try:
                    client.sock.settimeout(4)

                    responses.append(client.sock.recvfrom(406)) # 2 (message type size) + 4 (sequence number size) + 400 (info or key size)

                except socket.timeout: # If the first timeout occurs
                    if len(responses) == 0: # And none response was received, try again
                        datagram = (6).to_bytes(2, 'big') # Message type
                        datagram += (client.seqNum).to_bytes(4, 'big') # New Sequence Number

                        client.sock.sendto(datagram, (client.serventIp, client.serventPort))
                        client.seqNum += 1

                        while 1:
                            try:
                                client.sock.settimeout(4)

                                responses.append(client.sock.recvfrom(406)) # 2 (message type size) + 4 (sequence number size) + 400 (info or key size)

                            except socket.timeout: # If the second timeout occurs
                                if len(responses) == 0: # And none response was received
                                    print('Nenhuma resposta recebida.')
                                    return

                                else:
                                    Message.printResponses((client.seqNum-1).to_bytes(4, 'big'), responses) # If any response was received, print those
                                    return
                    else:
                        Message.printResponses((client.seqNum-1).to_bytes(4, 'big'), responses) # If any response was received, print those
                        return

    def printResponses(seqNum, responses): # Method to print the response
        for response in responses: # For each response received
            if response[0][2:6] == seqNum: # If the sequence number of the received message is the expected sequence number
                print((response[0][6:]).decode(), ' ', response[1][0], ':', response[1][1], sep='')

            else:
                print('Mensagem incorreta recebida de ', response[1][0], ':', response[1][1], sep='')


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
        client.sock.close() # Close the client socket
        print('Socket do client finalizado com sucesso.')
        break

    else:
        print('Comando invalido. Por favor, insira um novo comando.\n')

    print('')