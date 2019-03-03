import socket
import sys
import struct
import threading
import time

# usage: ./servidor.py

CONTADOR = 0
TIMEOUT = 15 # tempo que o server deve esperar para receber os dados (15 segundos)

def server_main():
    # cria socket. argumentos: (IPV4, TCP oriented)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    tv = struct.pack("ll", TIMEOUT, (1000*TIMEOUT)) # timeout
    s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDTIMEO, tv)

    HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
    PORT = 65432        # Port to listen on (non-privileged ports are > 1023)

    try:
        s.bind((HOST, PORT))
    except socket.error as e:
        print('Erro: '+str(e))

    # escuta conexões (parâmetro: número de clientes por vez, no caso 1)
    s.listen(1)

    while True:
        print('Aguardando conexão!')
        conn, addr = s.accept() # abre conexão entre cliente e servidor
        try:
            while True:
                data = conn.recv(40) # recebe os dados (40 bits = 5 bytes)                
                
                data = data.decode()

                result = decodeMsg(data)
                result = result.encode()

                if data:
                    ''' 
                        Transmite mensagem de volta (Valor do contador)
                            - Representada como string (ASCII), seis caracteres de 0 a 999999
                    '''
                    conn.sendall(result) 
                else:
                    break
                
        finally: # garante que conexão seja encerrada mesmo que haja erro
            # encerra conexão
            conn.close()


def decodeMsg(data):
    global CONTADOR
    if(data[0] == 1):
        CONTADOR = (CONTADOR + int(data[1:])) % 1000
    else:
        CONTADOR = (CONTADOR - int(data[1:])) % 1000
    
    return str(CONTADOR)


if __name__ == '__main__':
    server_main()