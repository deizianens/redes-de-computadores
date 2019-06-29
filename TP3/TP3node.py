'''
Responsável pelo armazenamento da base de dados chave-valor 
e pelo controle da troca de mensagens com seus parceiros
'''
import sys
import socket
import struct
import select

class Servent:
    def __init__(self):
        self.ip = '127.0.0.1'  # Local host IP
        self.port = int(sys.argv[1])
        self.sockets = {}
        self.neighborsPort = {}
        # List to store the messages received by each servent
        self.receivedMessagesList = []
        # Dictionary of keys given by the input file
        self.keyDictionary = {}  
        self.keyDictionaryConstructor()
        # Local port received from command line argument
        self.serventListConstructor()
        self.createSocket() # create servent socket
    
    # Method to construct the key dictionary from the input file
    def keyDictionaryConstructor(self):
        try:
            with open(sys.argv[2]) as f:
                line = f.readline()
                while line:
                    if(line[0] != "#"):
                        self.keyDictionary[ line.split(" ")[0] ] =  " ".join( line.split(" ")[1:]).replace('\n','')
                    line = f.readline()

        except AttributeError:
            print("Arquivo não encontrado.")
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except Exception as e:
            print(e)

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
     
    # Method to construct the servent list (connect to neighbor)
    def serventListConstructor(self):
        try:
            addresses = sys.argv[3:]
            for address in set(addresses):
                conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    conn.connect( (address.split(':')[0] , int( address.split(':')[1]) ) ) 
                    
                    # send id message to conect  
                    messageId = struct.pack('>h', 4) + struct.pack('>h', 0)   
                    conn.send(messageId)

                    self.sockets[(address.split(":")[0], int(address.split(":")[1]) )] = conn
                    self.neighborsPort[(address.split(":")[0], int(address.split(":")[1]) )] = 0

                except ConnectionRefusedError:
                    print("Falha de conexão")
                    raise KeyboardInterrupt
        except KeyboardInterrupt:
            raise KeyboardInterrupt

   
    def replyToClient(self ,nseq, data , ip , port):
        # +---- 2 ---+-- 4 -+--- 2 ---+----------\\---------------+
        # | TIPO = 9 | NSEQ | TAMANHO | VALOR (at´e 400 carateres) |
        # +----------+------+---------+----------\\---------------+
        messageRESP = struct.pack('>h', 9) + struct.pack('>i', nseq) + struct.pack('>h', len(data)) 
        messageRESP += str.encode( data )

        # Temporary connection to send the message.
        try:
            tempSocket = socket.socket(socket.AF_INET , socket.SOCK_STREAM)
            tempSocket.connect( ( ip, port ) )
            tempSocket.send( messageRESP )
            tempSocket.close()
            #print("Dado enviado: " , data)
        except socket.error as e:
            print("Falha ao enviar na porta recebida." , (ip, port) , e )

    def createKEYFLOODorTOPOFLOOD(self , tipo , ttl, nseq , ip_orig , porto_orig , tamanho , info , sentBy):
        #+---- 2 ------+- 2 -+-- 4 -+--- 4 ---+----- 2 ----+--- 2 ---+----------\\--------------+
        #| TIPO = 7, 8 | TTL | NSEQ | IP_ORIG | PORTO_ORIG | TAMANHO | INFO (até 400 carateres) |
        #+-------------+-----+------+---------+------------+---------+----------\\--------------+

        ttl -= 1 # decrease ttl before compare

        # repeated message or ttl expired. package can be thrown away and flooding canceled
        if( (ip_orig,porto_orig,nseq) in self.receivedMessagesList or ttl == 0):
            return

        # Used for treat repeat flooding
        self.receivedMessagesList.append( (ip_orig,porto_orig,nseq) )

        # If my db has this key, send this value to client:
        if( (tipo == 5 or tipo == 7) and info in self.db.keys()):
            # data = db value , ip = ip of sender , port = port that client gave me , nseq = came inside the package
            self.replyToClient(nseq ,  self.db[info] , ip_orig , porto_orig )

        # Topo requests add the own address and send to the client
        if( tipo == 6 or tipo == 8):
            info += str( socket.gethostbyname(socket.getfqdn())) + ":" + str(self.port) + " "  
            tamanho += len( str( socket.gethostbyname(socket.getfqdn()) ) + ":" + str(self.port) + " "   )
            self.replyToClient(nseq , info , ip_orig , porto_orig)

        # Flooding data
        message = (struct.pack('>h', tipo) +
            struct.pack('>h', ttl) +        # pack: > big-endian , h short integer - 2 bytes
            struct.pack('>i', nseq) +       # pack: > big-endian , i integer - 4 bytes
            socket.inet_aton( ip_orig ) +   # IPv4 address from dotted-quad string format (ex: ‘123.45.67.89’) to 32-bit packed binary format
            struct.pack('>h', porto_orig) + # pack: > big-endian , h short integer - 2 bytes
            struct.pack('>h', len(info)) +  # pack: > big-endian , h short integer - 2 bytes
            str.encode(info))
        
        # Send to all servents sockets
        for neighbor in self.sockets:
            if neighbor == '0':
                continue

            if self.neighborsPort[neighbor] == 0 and neighbor != sentBy :
                self.sockets[ neighbor ].send(message)



servent = Servent()  # Creates the servent object

try:
    while(servent.sockets):
        read_s, write_s, except_s = select.select([servent.sockets[sock] for sock in servent.sockets], [], [])

        for current_socket in read_s: 
            if current_socket is servent.sockets['0']: # servent socket 
                conn, client_address = current_socket.accept()
                conn.setblocking(0) # No timeouts.
                servent.sockets[client_address] = conn
            
            else:
                data = current_socket.recv(2)
                if data: # Connection is open yet

                            # ID   KEYREQ TOPOREQ KEYFLOOD TOPOFLOOD RESP
                            # 4    5      6       7        8         9
                            valueType = struct.unpack('>h', data)[0] 
                            
                            # ID
                            if(valueType == 4):
                                if current_socket.getpeername() not in servent.sockets:
                                    print("Mensagem ID recebida de algum desconhecido!")
                                    #os._exit(1)
                                    continue

                                # if another servent, port = 0 , otherwise port != 0
                                portOrZero = struct.unpack('>h', current_socket.recv(2) )[0]
                                servent.neighborsPort[ current_socket.getpeername() ] = portOrZero
                                #print("Recebida mensagem tipo 4 (ID) do porto:" , portOrZero)

                            # KEYREQ
                            elif(valueType == 5 ):
                                nseq = struct.unpack('>i', current_socket.recv(4) )[0] # unpack: > big-endian , i integer - 4 bytes
                                tamanho = struct.unpack('>h' , current_socket.recv(2))[0] # unpack: > big-endian , h short integer - 2 bytes
                                
                                searchedKey = ""
                                i=0
                                while( i < tamanho):
                                    searchedKey += bytes.decode( current_socket.recv(1) )
                                    i+=1

                                #print("começando a floodar, recebido de:" , sock.getpeername())
                                # Mounting KEYFLOOD MESSAGE 
                                servent.createKEYFLOODorTOPOFLOOD(7,4,nseq,current_socket.getpeername()[0], servent.neighborsPort[ current_socket.getpeername() ], len(searchedKey) , searchedKey, current_socket.getpeername())

                            # TOPOREQ - requests the network topology
                            elif(valueType == 6):
                                nseq = struct.unpack('>i', current_socket.recv(4) )[0] # unpack: > big-endian , i integer - 4 bytes
                                # Mounting KEYFLOOD MESSAGE 
                                servent.createKEYFLOODorTOPOFLOOD(8,4,nseq,current_socket.getpeername()[0] , servent.neighborsPort[current_socket.getpeername()],0,"", current_socket.getpeername() )
                            
                            # KEYFLOOD - receives a package, treats and spreads
                            elif(valueType == 7 or valueType == 8):
                                ttl = struct.unpack('>h', current_socket.recv(2) )[0]        # unpack: > big-endian , h short integer - 2 bytes
                                nseq = struct.unpack('>i', current_socket.recv(4) )[0]       # unpack: > big-endian , i integer - 4 bytes
                                ip_orig = socket.inet_ntoa( current_socket.recv(4) )         # Convert a 32-bit packed IPv4 address (a string four characters in length) to its standard dotted-quad string
                                porto_orig = struct.unpack('>h', current_socket.recv(2) )[0] # unpack: > big-endian , h short integer - 2 bytes
                                tamanho = struct.unpack('>h', current_socket.recv(2) )[0]    # unpack: > big-endian , h short integer - 2 bytes
                                
                                info = ""
                                i=0
                                while( i < tamanho):
                                    info += bytes.decode( current_socket.recv(1) )
                                    i+=1

                                # Mounting KEYFLOOD MESSAGE 
                                servent.createKEYFLOODorTOPOFLOOD(valueType,ttl,nseq,ip_orig,porto_orig,len(info),info , current_socket.getpeername())
                else:
                            # Interpret empty result as closed connection
                            #print ('Fechando conexão com ', sock.getpeername(), ', pois o outro lado já está fechado.')
                            # Stop listening for input on the connection
                            del servent.sockets[current_socket.getpeername()]
                            current_socket.close()
except KeyboardInterrupt:
            raise KeyboardInterrupt

