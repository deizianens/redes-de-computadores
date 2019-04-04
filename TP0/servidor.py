import socket
import sys
import struct
import time

# usage: ./servidor.py <port>

CONTADOR = 0
TIMEOUT = 15 # tempo que o server deve esperar para receber os dados (15 segundos)
MSG_SIZE = 5 # 5 bytes (1 OPERADOR + Inteiro de 4 bytes)

def server_main(p):
    # cria socket. argumentos: (IPV4, TCP oriented)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    tv = struct.pack("ll", TIMEOUT, 0) # timeout
    s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, tv)

    HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
    PORT = p            # Port to listen on (non-privileged ports are > 1023)

    try:
        s.bind((HOST, PORT))
    except socket.error as e:
        print('Erro: '+str(e))

    # escuta conexões (parâmetro: número de clientes por vez, no caso 1)
    s.listen(1)

    while True:
        # print('Aguardando conexão!')
        conn, addr = s.accept() # abre conexão entre cliente e servidor

        # print ('Conectado por', addr)
        
        try:
            while True:
                data = conn.recv(MSG_SIZE) # recebe os dados                

                if data:
                    data = data.decode('ascii')

                    result = decode_msg(str(data))
                    result = format(result, '06d') # resposta deve ter 6 dígitos
                    result = result.encode('ascii')
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


def decode_msg(data):
    global CONTADOR
    op = data[0] 
    value = data[1:]

    value = struct.unpack("!I", value)
    value = value[0]

    if(op == '1'):
        CONTADOR = (CONTADOR + value) % 1000000
    else:
        CONTADOR = (CONTADOR - value) % 1000000
    
    # print('Contador: ', CONTADOR)
    return CONTADOR


if __name__ == '__main__':
    PORT =  int(sys.argv[1])     # Port: porta
    server_main(PORT)