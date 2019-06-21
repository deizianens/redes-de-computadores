'''
Receberá do usuário as chaves que devem ser consultadas ´
e exibirá os resultados que forem recebidos para as consultas.
'''
import sys
import socket

class ClientInfo: # Class to represent each client
	def __init__(self):
		self.serventIp, self.serventPort = sys.argv[1].split(':') # Gets the servent ip and port from the command line argument
		self.serventPort = int(self.serventPort) # Casts the port to be a int
		self.seqNum = 0 # Attribute to sabe the actual sequence number of the client
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP socket creation
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Option to reuse the socket address to stop giving the error: Adress is already being used when running the program multiple times

class Message: # Class to represent the client message methods
	def sendKeyReq(client, message): # Method to send a keyReq message to a servent
		datagram = (5).to_bytes(2, 'big') # Message type
		datagram += (client.seqNum).to_bytes(4, 'big') # Sequence Number
		datagram += message[0:400].encode('ascii') # Required Key

		client.sock.sendto(datagram, (client.serventIp, client.serventPort))
		client.seqNum += 1

		responses = [] # List to store the responses
		while 1:
			try:
				client.sock.settimeout(4)

				responses.append(client.sock.recvfrom(406)) # 2 (message type size) + 4 (sequence number size) + 400 (info or key size)

			except socket.timeout: # If the first timeout occurs
				if len(responses) == 0: # And none response was received, try again
					datagram = (5).to_bytes(2, 'big') # Message type
					datagram += (client.seqNum).to_bytes(4, 'big') # New Sequence Number
					datagram += message[0:400].encode('ascii') # Required Key

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

	def sendTopoReq(client): # Method to send a topoReq message to a servent
			datagram = (6).to_bytes(2, 'big') # Message type
			datagram += (client.seqNum).to_bytes(4, 'big') # Sequence Number

			client.sock.sendto(datagram, (client.serventIp, client.serventPort))
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


client = ClientInfo() # Creates the object to represent the client

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