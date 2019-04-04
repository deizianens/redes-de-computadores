import socket
import sys
import struct
import threading
import time

# usage: ./cliente.py <host> <port>

TIMEOUT = 15 # tempo que o server deve esperar para receber os dados (15 segundos)

# classe que gera os clientes
class Cliente(threading.Thread):
    def __init__(self, c, host, port):
        self.c = c          # numero de identificação do cliente
        self.host = host    # servidor a ser conectado
        self.port = port    # porto

        threading.Thread.__init__(self)

    def run(self):

        tv = struct.pack("ll", TIMEOUT, 0) # timeout
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, tv)
        
        try:
            s.connect((self.host, self.port)) # Estabelece conexão.
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except socket.error as e:
            print('Falha de conexão: '+str(e))
            sys.exit()

        msg = get_msg() # lê comando do teclado

        while(1):
            s_msg = encode_msg(msg) 
            s.send(s_msg)

            data = s.recv(1024) # recebe resposta do servidor
            print(data.decode('ascii'))

            msg = get_msg() # lê comando do teclado

        s.close() # fecha conexão


def encode_msg(msg):
    data = msg.split(" ") # toda mensagem consiste em sinal + espaço + valor (e.g + 123)
    op = data[0]
    value = data[1]

    if(op == '+'):
        op = '1'
    elif (op == '-'):
        op = '0'

    encoded_value = struct.pack("!I", int(value)) # !I = network byte order unsigned int
    return op + encoded_value

def get_msg(): 
	entrada = input()
	if entrada: 
		return entrada


if __name__ == '__main__':
    HOST =  sys.argv[1]     # Host: endereço IP
    PORT = int(sys.argv[2]) # Port: porto 

    for i in range(1):
        Cliente(i, HOST, PORT).start()