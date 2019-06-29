#!/usr/bin/python3

# __________________________
# |  TP 3 - Redes - P2P     |
# |  Marcelo Nunes da Silva |
# |  Wanderson Sena         |
# |_________________________|

# Commands:
# ? chave -> procura um valor na rede, passando uma chave buscada.
# T -> Solicita a topologia da rede
# Q -> Sair

import socket , sys , os , struct , select

class TP3client:
    def __init__(self):
        if(len(sys.argv) < 3): 
            print("./TP3client <porto-local> <ip:porto>")
            os._exit(1)

        try:
            # Input data from terminal
            self.port = sys.argv[1]
            self.serverIp = sys.argv[2]

            # List of sockets
            self.socketsList = { }
            self.socketsList['stdin'] = sys.stdin

            # Number of sequence, to treat repeated cases
            self.nseq = 0

            # Create accept socket and the socket to communicate with the servent.
            self.createInitialSockets()

            # Start to listen the user commands and the answer received from the servents
            self.listenCommandsAndAnswers()
        except KeyboardInterrupt:
            for con in self.socketsList:
                self.socketsList[con].close() 
            os._exit(1)

    def createInitialSockets(self):
        # 0 = self socket (listening to answers) ,  self.serverIp = servent
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create a TCP/IP socket
            
            # Bind the socket to the port
            #print ('Escutando no endereço "'+ str( socket.gethostbyname(socket.getfqdn()) ) +'" e port "'+ self.port +'"')
            #print('-'*20)
            client.bind(("", int(self.port)))
            # Listen for incoming connections
            client.listen()

          

            self.socketsList['0'] = client

        except socket.error as e:
            print ('Falha ao conectar com o servent informado.' , e)
            os._exit(1)
            

        # Servent socket
        try:
            servent = socket.socket(socket.AF_INET, socket.SOCK_STREAM)# Create a TCP/IP socket
            servent.connect( ( self.serverIp.split(':')[0] , int( self.serverIp.split(':')[1] ) ) ) # connect to servent

            # > big-endian, padrão do TCP/IP
            # h short integer - 2 bytes
            messageId = struct.pack('>h', 4) + struct.pack('>h', int(self.port))   

            # messageId is used to warn the other side
            servent.send( messageId )
            # Sockets from which we expect to read
            self.socketsList[ self.serverIp]  = servent
        except ConnectionRefusedError:
            print("Connection failure. " , self.serverIp)
            os._exit(1)
        except socket.error:
            print ('Could not connect to servent ')
            os._exit(1)
            
    def listenCommandsAndAnswers(self):
        try:
            while(1):
                # Get the list sockets which are readable
                read_sockets, write_sockets, error_sockets = select.select( [ self.socketsList[sockeet] for sockeet in self.socketsList ], [], [] )
                
                for sock in read_sockets:

                    # ---------  Listen prompt commands  -------------------
                    if sock is self.socketsList['stdin']:

                        # read command and remove \n or \0 to avoid mistakes
                        command = sock.readline().replace('\0',"").replace('\n',"")
                        
                        if(command == "" or command == "?"):
                            print("Comando desconhecido")
                            continue
                        
                        elif ( (command[0] == "?" and (command[1] == " " or command[1] == '\t')) or (command == "T" or command == 't') ):
                            
                            # Before send request, update the nseq value
                            self.nseq += 1

                            # --------------- KEYREQ MESSAGE -----------------
                            if(command[0] == "?" and (command[1] == " " or command[1] == '\t')):
                                searchedKey = command[2:]
                                messageKEYREQorTOPOREQ = struct.pack('>h', 5) + struct.pack('>i', self.nseq) + struct.pack('>h', len(searchedKey)) 
                                messageKEYREQorTOPOREQ += str.encode(searchedKey)

                            # -------------- TOPOREQ MESSAGE ----------------
                            if(command == "T" or command == 't'):
                                messageKEYREQorTOPOREQ = struct.pack('>h', 6) + struct.pack('>i', self.nseq)

                            # Ask for the value in the key entered by the user
                            self.socketsList[self.serverIp].send( messageKEYREQorTOPOREQ )

                            # Count for 4 seconds for a connection respond
                            try:
                                self.socketsList['0'].settimeout(4)
                                connection, client_address = self.socketsList['0'].accept()
                                self.socketsList[client_address] = connection
                                
                            except socket.timeout:
                                print("Nenhuma resposta recebida")                   

                        elif(command == "Q" or command == 'q'):
                            raise KeyboardInterrupt
                        else:
                            print("Comando desconhecido")
                    

                    elif sock is self.socketsList['0']:
                        # Giving chance to another to respond
                        try:
                            connection, client_address = sock.accept()
                            self.socketsList[client_address] = connection
                        except socket.timeout:
                            continue
                    # ----------   Data is comming ------------------------
                    else:
                        #  RESP 
                        #+---- 2 ---+-- 4 -+--- 2 ---+----------\\---------------+
                        #| TIPO = 9 | NSEQ | TAMANHO | VALOR (até 400 carateres) |
                        #+----------+------+---------+----------\\---------------+
                        data = sock.recv(2) # receive message type
                        if data: 

                            # TIPO
                            valueType = struct.unpack('>h', data)[0] 
                            if valueType == 9:

                                # NSEQ   
                                nseq = struct.unpack('>i', sock.recv(4))[0]
                                if nseq != self.nseq:
                                    print("Mensagem incorreta recebida de ", str(sock.getpeername()[0]) + ":" + str(sock.getpeername()[1]))
                                
                                else:
                                    # TAMANHO
                                    tamanho =  struct.unpack('>h', sock.recv(2))[0]
                                    i=0
                                    returnedValue = ""
                                    # VALOR
                                    while(i < tamanho):
                                        returnedValue += bytes.decode( sock.recv(1) )
                                        i+=1

                                    print(returnedValue , str(sock.getpeername()[0])+":"+str(sock.getpeername()[1]))

                                # Remove connection
                                del self.socketsList[ sock.getpeername() ]
                                sock.close()
                        else:
                            raise KeyboardInterrupt
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:
            print("Linha 177:",e)
            raise

if __name__ == "__main__":
    node = TP3client()