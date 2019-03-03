import socket
import sys
import struct
import threading
import time

# usage: ./app-server.py <host> <port>

TIMEOUT = 15 # tempo que o server deve esperar para receber os dados (15 segundos)

def server_main():
    # cria socket. argumentos: (IPV4, TCP oriented)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
    PORT = 65432        # Port to listen on (non-privileged ports are > 1023)

    try:
        s.bind((HOST, PORT))
    except socket.error as e:
        print('Erro: '+str(e))

    # escuta conexões (parâmetro: número de clientes por vez, no caso 1)
    s.listen(1)

    #timeout
    # timeval = struct.pack('ll', TIMEOUT, usec)
    # s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, timeval)

    while True:
        print('Aguardando conexão!')
        conn, addr = s.accept() # abre conexão entre cliente e servidor
        print('Conectado com ', addr)

        try:
            while True:
                data = conn.recv(40) # recebe os dados (40 bits = 5 bytes)

                print ('Recebeu "%s"' % data)

                if data:
                    print ('Enviando dados de volta para cliente')
                    ''' 
                        Transmite mensagem de volta (Valor do contador)
                            - Representada como string (ASCII), seis caracteres de 0 a 999999
                    '''
                    conn.sendall(data) 
                else:
                    print ('Sem mais dados de ', addr)
                    break
                
        finally: # garante que conexão seja encerrada mesmo que haja erro
            # encerra conexão
            conn.close()


if __name__ == '__main__':
    server_main()