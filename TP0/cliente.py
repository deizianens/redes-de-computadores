import socket
import sys
import struct
import threading

# usage: ./app-server.py <host> <port>

TIMEOUT = 15 # tempo que o server deve esperar para receber os dados (15 segundos)

# classe que gera os clientes
class Cliente(threading.Thread):
    def __init__(self, c, host, port, *mensagem):
        self.c = c          # numero de identificação do cliente
        self.host = host    # servidor a ser conectado
        self.port = port
        self.msg = mensagem

        threading.Thread.__init__(self)

    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            s.connect((self.host, self.port)) # Estabelece conexão.
        except socket.error as e:
            print('Falha de conexão: '+str(e))
            sys.exit()
        
        s.send(msg)

        data = s.recv(1024) # recebe resposta do servidor
        print(data)

        s.close()


if __name__ == '__main__':
    HOST =  sys.argv[1]     # Host: endereço IP
    PORT = int(sys.argv[2]) # Port: porto 
    m = input()
    msg = m.encode()

    for i in range(1):
        Cliente(i, HOST, PORT, *msg).start()