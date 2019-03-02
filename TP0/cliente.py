# usage: ./app-server.py <host> <port>

import socket
import sys
import struct

def client_main():
    # cria socket. argumentos: (IPV4, TCP oriented)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # 192.168.1.6
    HOST =  sys.argv[1]     # Host: endereço IP
    PORT = int(sys.argv[2]) # Port: porto 

    try:
        s.connect((HOST, PORT)) # Estabelece conexão.
    except socket.error as e:
        print('Falha de conexão: '+str(e))
        sys.exit()

    '''
        Mensagem a ser enviada:
            - 1 byte = operação a ser realizada (0 subtração, 1 adição)
            - 4 bytes = número inteiro codificado em network byte order
    '''
    msg = input()

    # Converte mensagem para ASCII
    msg.encode('ascii')

    p_size = struct.pack('!i', msg)
    s.send(p_size)
    s.recv(32)

    s.close()

if __name__ == '__main__':

    client_main()