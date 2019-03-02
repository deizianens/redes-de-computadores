# usage: ./app-server.py <host> <port>

import socket
import sys
import struct
import threading

def server_main():
    # cria socket. argumentos: (IPV4, TCP oriented)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
    PORT = 65432        # Port to listen on (non-privileged ports are > 1023)

    try:
        s.bind((HOST, PORT))
    except socket.error as e:
        print('Erro: '+str(e))

    # escuta conexões
    s.listen(5)

    while True:
        print('Aguardando conexão!')
        conn, addr = s.accept() # abre conexão entre cliente e servidor

        try:
            while True:
                data = conn.recv(40) # recebe os dados (40 bits = 5 bytes)
                
                print (sys.stderr, 'received "%s"' % data)
                if data:
                    print ('sending data back to the client')
                    ''' 
                        Transmite mensagem de volta (Valor do contador)
                            - Representada como string (ASCII), seis caracteres de 0 a 999999
                    '''
                    conn.sendall(data) 
                else:
                    print ('no more data from', addr)
                    break
                
        finally: # garante que conexão seja encerrada mesmo que haja erro
            # encerra conexão
            conn.close()


if __name__ == '__main__':
    server_main()