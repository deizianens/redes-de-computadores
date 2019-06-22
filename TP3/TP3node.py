'''
Responsável pelo armazenamento da base de dados chave-valor 
e pelo controle da troca de mensagens com seus parceiros
'''
import sys
import socket

class ServentInfo: # Class to represent each servent
    # ./TP3node <porto-local> <banco-chave-valor> [ip1:porto1 [ip2:porto2 ...]]
    def __init__(self):
        self.ip = '127.0.0.1' # Local host IP
        self.port = int(sys.argv[1]) # Local port received from command line argument
        self.keyDictionaryConstructor(sys.argv[2])
        self.serventListConstructor(sys.argv[3])
        
        self.keyDictionary = {} # Dictionary of keys given by the input file

        self.ipBinary = [] # List of binary numbers that represents the IP
        self.ipBinaryConstructor()
        self.receivedMessagesList = [] # List to store the messages received by each servent
        
        self.createSocket()

    def createSocket(self):
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP socket creation
            server_socket.setblocking(0)
            server_socket.bind(('', int(self.port)))
            server_socket.listen()

            self.socketsList['0'] = server_socket
        except:
            print("Erro ao criar socket(1).")
            sys.exit()

    def ipBinaryConstructor(self): # Method to construct the binary ip
        self.ipBinary.append((127).to_bytes(1, 'big'))
        self.ipBinary.append((0).to_bytes(1, 'big'))
        self.ipBinary.append((0).to_bytes(1, 'big'))
        self.ipBinary.append((1).to_bytes(1, 'big'))

    def keyDictionaryConstructor(self, inputFile): # Method to construct the key dictionary from the input file
        file = open(inputFile, 'r')
        keys = file.readlines()

        for key in keys:
            if key[0] != '#': # If the first character from the line isn't a comment (#)
                key = key.split()
                self.keyDictionary[key[0]] = str.join(' ',(key[1:])) # Save the key and the value in the key Dictionary

    def serventListConstructor(self, servents): # Method to construct the servent list
        command = "[('"
        command += servents[1:].replace('[',"),('").replace(']','').replace(':',"',") # Transform the list [127.0.0.1:55555[127.0.0.1:55556]] to [('127.0.0.1',55555),('127.0.0.1',55556)], which is the way that Python deals with list of tuples
        command += ')]'
        self.serventList = eval(command) # Evaluate the command above

    def checkMessageIsNew(self, recvMsg): # Method to check if the received message is new in the servent by looking into the receivedMessagesList
        for savedMsg in self.receivedMessagesList:
            if savedMsg[0] == recvMsg[8:14] and savedMsg[1] == recvMsg[4:8]:
                return False

        self.receivedMessagesList.append((recvMsg[8:14],recvMsg[4:8])) # If the message is new, insert the message in the receivedMessagesList
        return True

class Message: # Class to represent the servent message methods
    '''
    KEYFLOOD, TOPOFLOOD (valor do tipo indica o tipo de mensagem)
    +---- 2 ------+-- 2 --+--- 4 --+--- 4 ---+----- 2 ----+----------\\-------------------+
    | TIPO = 7, 8 | TTL | NSEQ | IP_ORIG | PORTO_ORIG | INFO (up to 400 characteres) |
    +-------------+-------+--------+---------+------------+----------\\-------------------+
    '''
    def recvKeyReq(servent, clientAddress, recvMsg): # Method to deal with keyReq messages
        keyFloodMsg = (7).to_bytes(2, 'big') # Message type
        keyFloodMsg += (3).to_bytes(2, 'big') # TTL
        keyFloodMsg += recvMsg[2:6] # Sequence Number
        keyFloodMsg += servent.ipBinary[0] # First byte of the binary client ip
        keyFloodMsg += servent.ipBinary[1] # Second byte of the binary client ip
        keyFloodMsg += servent.ipBinary[2] # Third byte of the binary client ip
        keyFloodMsg += servent.ipBinary[3] # Fourth byte of the binary client ip
        keyFloodMsg += (clientAddress[1]).to_bytes(2, 'big') # Client port
        keyFloodMsg += recvMsg[6:] # Required Key

        if servent.checkMessageIsNew(keyFloodMsg):

            if recvMsg[6:].decode() in servent.keyDictionary: # If this servent has the key in his keyDictionary, send a resp to the client
                Message.sendRespFromKeyReq(servent, clientAddress, recvMsg)

            Message.sendMessageToServentList(servent, keyFloodMsg)

    def recvTopoReq(servent, clientAddress, recvMsg): # Method to deal with topoReq messages
        topoFloodMsg = (8).to_bytes(2, 'big') # Message type
        topoFloodMsg += (3).to_bytes(2, 'big') # TTL
        topoFloodMsg += recvMsg[2:6] # Sequence Number
        topoFloodMsg += servent.ipBinary[0] # First byte of the binary client ip
        topoFloodMsg += servent.ipBinary[1] # Second byte of the binary client ip
        topoFloodMsg += servent.ipBinary[2] # Third byte of the binary client ip
        topoFloodMsg += servent.ipBinary[3] # Fourth byte of the binary client ip
        topoFloodMsg += (clientAddress[1]).to_bytes(2, 'big') # Client Port
        topoFloodMsg += (servent.ip).encode('ascii') # Actual servent ip
        topoFloodMsg += ':'.encode('ascii')
        topoFloodMsg += (str(servent.port)).encode('ascii') # Actual servent port

        if servent.checkMessageIsNew(topoFloodMsg):
            Message.sendRespFromTopoReq(servent, clientAddress, recvMsg, topoFloodMsg)
            Message.sendMessageToServentList(servent, topoFloodMsg)

    def recvKeyFlood(servent, recvMsg): # Method to deal with keyFlood messages
        if recvMsg[14:].decode() in servent.keyDictionary: # If the key is in the keyDictionary
            Message.sendRespFromKeyFlood(servent, recvMsg)

        keyFloodMsg = Message.decrementTTL(recvMsg)

        if Message.TTLIsValid(keyFloodMsg): # if valid TTL, continue, else discard
            Message.sendMessageToServentList(servent, keyFloodMsg)

    def recvTopoFlood(servent, recvMsg): # Method to deal with topoFlood messages
        topoFloodMsg = (8).to_bytes(2, 'big') # Message type
        topoFloodMsg += recvMsg[2:4] # TTL
        topoFloodMsg += recvMsg[4:8] # Sequence Number
        topoFloodMsg += recvMsg[8:14] # IP and Port from the client
        topoFloodMsg += recvMsg[14:] # Actual sent info
        topoFloodMsg += ' '.encode('ascii')
        topoFloodMsg += (servent.ip).encode('ascii') # Actual servent ip
        topoFloodMsg += ':'.encode('ascii')
        topoFloodMsg += (str(servent.port)).encode('ascii') # Actual servent port

        Message.sendRespFromTopoFlood(servent, topoFloodMsg)

        topoFloodMsg = Message.decrementTTL(topoFloodMsg)

        if Message.TTLIsValid(topoFloodMsg): # if valid TTL, continue, else discard
            Message.sendMessageToServentList(servent, topoFloodMsg)

    def sendRespFromKeyReq(servent, clientAddress, recvMsg): # Method to send the resp message to the client from a keyReq
        newMessage = (9).to_bytes(2, 'big') # Message type
        newMessage += recvMsg[2:6] # Sequence Number
        newMessage += servent.keyDictionary[recvMsg[6:].decode()].encode('ascii') # Key value

        servent.sock.sendto(newMessage, clientAddress)

    def sendRespFromTopoReq(servent, clientAddress, recvMsg, topoFloodMsg): # Method to send the resp message to the client from a topoReq
        newMessage = (9).to_bytes(2, 'big') # Message type
        newMessage += recvMsg[2:6] # Sequence Number
        newMessage += topoFloodMsg[14:] # Actual topology to reach the actual servent

        servent.sock.sendto(newMessage, clientAddress)

    '''
    RESP
    +---- 2 ---+-- 4 -+--- 2 ---+----------\\---------------+
    | TIPO = 9 | NSEQ | TAMANHO | VALOR (up to 400 carateres) |
    +----------+------+---------+----------\\---------------+
    '''
    def sendRespFromKeyFlood(servent, recvMsg): # Method to send the resp message to the client from a keyFlood
        clientAddress = Message.clientAddressConstructor(recvMsg)

        respMessage = (9).to_bytes(2, 'big') # Message type
        respMessage += recvMsg[4:8] # Sequence Number
        respMessage += recvMsg[14:16] # Message size
        respMessage += servent.keyDictionary[recvMsg[16:].decode()].encode('ascii') # Key value

        servent.sock.send(respMessage)

    def sendRespFromTopoFlood(servent, topoFloodMsg): # Method to send the resp message to the client from a topoFlood
        clientAddress = Message.clientAddressConstructor(topoFloodMsg)

        respMessage = (9).to_bytes(2, 'big') # Message type
        respMessage += topoFloodMsg[4:8] # Sequence Number
        respMessage += recvMsg[14:16] # Message size
        respMessage += topoFloodMsg[16:] # Actual topology to reach the actual servent

        servent.sock.send(respMessage)

    def sendMessageToServentList(servent, message): # Method to send the message to all servents in the servent list
        for serv in servent.serventList:
            servent.sock.sendto(message, (serv[0], serv[1]))

    def clientAddressConstructor(message): # Method to construct the client address to auxiliate the resp message methods
        clientPort = int.from_bytes(message[12:14], 'big')

        return ('127.0.0.1', clientPort)

    def decrementTTL(message): # Method to decrement the TTL and return the new message 
        ttlValue = int.from_bytes(message[2:4], 'big') # TTL value
        ttlValue -= 1
        newMessage = message[0:2] # Message type
        newMessage += ttlValue.to_bytes(2, 'big') # New TTL value
        newMessage += message[4:] # Rest of the message

        return newMessage

    def TTLIsValid(message): # Method to verify the TTL value
        return True if int.from_bytes(message[2:4], 'big') > 0 else False


servent = ServentInfo() # Creates the servent object

while 1:
   
    # 2 (message type size) + 2 (TTL size) + 4 (sequence number size) + 4 (IP origin size) + 2 (port origin size) + 400 (info or key size)
    recvMsg, recvAddress = servent.sock.recvfrom(414) 

    if recvMsg[0:2] == (5).to_bytes(2, 'big'):
        Message.recvKeyReq(servent, recvAddress, recvMsg)

    elif recvMsg[0:2] == (6).to_bytes(2, 'big'):
        Message.recvTopoReq(servent, recvAddress, recvMsg)

    elif recvMsg[0:2] == (7).to_bytes(2, 'big'):
        if servent.checkMessageIsNew(recvMsg):
            Message.recvKeyFlood(servent, recvMsg)

    elif recvMsg[0:2] == (8).to_bytes(2, 'big'):
        if servent.checkMessageIsNew(recvMsg):
            Message.recvTopoFlood(servent, recvMsg)