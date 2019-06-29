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
        read_sockets, write_sockets, error_sockets = select.select(
            [client.sockets[sockeet] for sockeet in client.sockets], [], [])

        for sock in read_sockets:
                if sock is client.sockets['stdin']:
                    
                        command = sock.readline().replace('\0', "").replace('\n', "")

                        if(command == "" or command == "?"):
                            print("Comando desconhecido")
                            continue

                        elif ((command[0] == "?" and (command[1] == " " or command[1] == '\t')) or (command == "T" or command == 't')):

                            # --------------- KEYREQ MESSAGE -----------------
                            if(command[0] == "?" and (command[1] == " " or command[1] == '\t')):
                                searchedKey = command[2:]
                                messageKEYREQorTOPOREQ = struct.pack('>h', 5) + struct.pack('>i', client.seqNum) + struct.pack('>h', len(searchedKey)) 
                                messageKEYREQorTOPOREQ += str.encode(searchedKey)

                            # -------------- TOPOREQ MESSAGE ----------------
                            if(command == "T" or command == 't'):
                                messageKEYREQorTOPOREQ = struct.pack('>h', 6) + struct.pack('>i', client.seqNum)

                            # Ask for the value in the key entered by the user
                            client.sockets[client.ipPort].send( messageKEYREQorTOPOREQ )

                            # Count for 4 seconds for a connection respond
                            try:
                                client.sockets['0'].settimeout(4)
                                connection, client_address = client.sockets['0'].accept()
                                client.sockets[client_address] = connection
                                
                            except socket.timeout:
                                print("Nenhuma resposta recebida")     

                        elif(command == "Q" or command == 'q'):
                            raise KeyboardInterrupt
                        else:
                            print("Comando desconhecido")

                elif sock is client.sockets['0']:
                        # Giving chance to another to respond
                        try:
                            connection, client_address = sock.accept()
                            client.sockets[client_address] = connection
                        except socket.timeout:
                            continue

                else:
                        #  RESP
                        #+---- 2 ---+-- 4 -+--- 2 ---+----------\\---------------+
                        #| TIPO = 9 | NSEQ | TAMANHO | VALOR (até 400 carateres) |
                        #+----------+------+---------+----------\\---------------+
                        data = sock.recv(2)  # receive message type
                        if data:

                            # TIPO
                            valueType = struct.unpack('>h', data)[0]
                            if valueType == 9:

                                # NSEQ
                                nseq = struct.unpack('>i', sock.recv(4))[0]
                                if nseq != client.seqNum:
                                    print("Mensagem incorreta recebida de ", str(
                                        sock.getpeername()[0]) + ":" + str(sock.getpeername()[1]))

                                else:
                                    # TAMANHO
                                    tamanho = struct.unpack(
                                        '>h', sock.recv(2))[0]
                                    i = 0
                                    returnedValue = ""
                                    # VALOR
                                    while(i < tamanho):
                                        returnedValue += bytes.decode(
                                            sock.recv(1))
                                        i += 1

                                    print(returnedValue, str(sock.getpeername()[
                                          0])+":"+str(sock.getpeername()[1]))

                                # Remove connection
                                del client.sockets[sock.getpeername()]
                                sock.close()
                        else:
                            raise KeyboardInterrupt
except KeyboardInterrupt:
    raise KeyboardInterrupt
except Exception as e:
    print(e)
    raise
