# encoding=utf-8

'''
    DCCNET - Trabalho Prático 1
    Redes de Computadores 2019/01
    Deiziane Natani da Silva - 2015121980

'''
import sys, os
import socket
import time
import threading
import binascii
import struct

MAX_DATA = 512 # 512 bytes
SOF = 'cc'
EOF = 'cd'
DLE = '1b'
ACK = '80'      # 128
DATA = '7f'     # 127

original_data = b'' # é necessário a mensagem sem byte stuffing para calcular o checksum

class Data:
    def __init__(self, data='', id=1, flags=127):
        self.data = data
        self.confirmed = False
        self.id = id
        self.flags = flags

    def prepare_data(self):
        self.confirmed = False
        self.id = 1 if self.id == 0 else 0 # muda id (alterna entre 0 e 1)

    @staticmethod
    def _format_numbers(number, is_2_bytes=True):
        pattern = '{:04x}' if is_2_bytes else '{:02x}'
        return pattern.format(number)

    '''
        Formato de um quadro DCCNET
        SOF    | ID      | flags   | checksum   | dados          | EOF
        1 byte | 1 byte  | 1 byte  | 2 bytes    | max 512 bytes  | 1 byte

    '''
    def checksum(self):
        data = SOF #  início de um novo quadro
        data += self._format_numbers(self.id, False)
        data += self._format_numbers(self.flags, False)
        data += self._format_numbers(0)
        data = binascii.unhexlify(data.encode()) + original_data

        checksum = 0
        pointer = 0
        size = len(data)

        while size > 1:
            checksum += int(str('%02x' % (data[pointer],)) + str('%02x' % (data[pointer + 1],)), 16)
            size -= 2
            pointer += 2
        if size:
            checksum += data[pointer]

        checksum = (checksum >> 16) + (checksum & 0xffff)
        checksum += (checksum >> 16)

        return (~checksum) & 0xFFFF

    # encrypt
    def encode16(self, new_data):
        return binascii.hexlify(new_data)

    # decrypt
    def decode16(self, new_data):
        self.data = binascii.unhexlify(new_data)

    def get_frame(self):
        formatted_id = self._format_numbers(self.id, False)
        formatted_flags = self._format_numbers(self.flags, False)
        formatted_checksum = self._format_numbers(self.checksum())
        encoded_data = self.encode16(self.data)
        header = (formatted_id + formatted_flags + formatted_checksum).encode()
        return header + encoded_data + EOF.encode() 


d_send = Data(id=0)
d_rcv = Data()
timeout = False


'''
    Inicializa cliente:
    ./dccnet -c <IP>:<PORT> <INPUT> <OUTPUT>
    Parâmetros: 
        - Endereço IP da máquina 
        - Porta, 
        - Nome de um arquivo com os dados que devem ser enviados, 
        - Nome de um arquivo onde os dados recebidos devem ser armazenados

'''
def init_client():
    IP = sys.argv[2].split(':')[0]
    PORT = int(sys.argv[2].split(':')[1])
    INPUT = sys.argv[3]
    OUTPUT = sys.argv[4]

    # Deleta caminho antigo de output
    if os.path.exists(OUTPUT):
        os.remove(OUTPUT)

    # Conexão TCP
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    connection.connect((IP, PORT))

    # Threads para enviar e receber (paralelamente)
    s_thread = threading.Thread(target=send_data, args=(connection, INPUT))
    s_thread.start()
    rcv_thread = threading.Thread(target=receive_data, args=(connection, OUTPUT))
    rcv_thread.start()


'''
    Inicializa servidor:
    ./dccnet -s <PORT> <INPUT> <OUTPUT>
    Parâmetros: 
        - Porta, 
        - Nome de um arquivo com os dados que devem ser enviados, 
        - Nome de um arquivo onde os dados recebidos devem ser armazenados

'''
def init_server():
    IP = '127.0.0.1' # localhost
    PORT = int(sys.argv[2])
    INPUT = sys.argv[3]
    OUTPUT = sys.argv[4]

    if os.path.exists(OUTPUT):
        os.remove(OUTPUT)
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except socket.error:
        print("Erro ao criar socket!")
        exit(2)
    
    try:
        s.bind((IP, PORT))
        s.listen(1)
        print('SERVER na porta ' + str(PORT))
        connection, addr = s.accept()
    except KeyboardInterrupt:
        s.close()
        sys.exit(0)

    #Threads para enviar e receber 
    s_thread = threading.Thread(target=send_data, args=(connection, INPUT))
    s_thread.start()
    rcv_thread = threading.Thread(target=receive_data, args=(connection, OUTPUT))
    rcv_thread.start()


'''
    Formato de um quadro DCCNET
    SOF    | ID      | flags   | checksum   | dados          | EOF
    1 byte | 1 byte  | 1 byte  | 2 bytes    | max 512 bytes  | 1 byte

'''
def send_data(con, file_name):
    cnt = MAX_DATA
    original_msg = b''
    msg = b''

    with open(file_name, 'rb') as file:
        line = file.read(1) 

        # lê os 512 bytes maximos
        while (cnt > 0 and line):
            aux = d_send.encode16(line)
            aux2 = line
            
            # caso seja DLE ou EOF, temos que fazer o byte stuffing
            if aux == DLE or aux == EOF: 
                msg += DLE
                cnt -= 1
            
            msg += aux
            original_msg += aux2
            cnt -= 1 
            if cnt > 0:
                line = file.read(1) 

        d_send.data = msg
        global original_data
        original_data = original_msg
        print('Dados enviados de: ' + file_name)

        con.send(SOF.encode())
        con.send(d_send.get_frame())

        global timeout
        timeout = False

        def handle_timeout():
            global timeout
            timeout = True

        timer = threading.Timer(1, handle_timeout)
        timer.start()
        while True:
            if timeout:
                print('Erro: ACK não foi recebido!')
                break

            if d_send.confirmed:
                line = file.read(MAX_DATA)
                d_send.prepare_data()
                break


def receive_data(con, file_name):
    id = 1 # id do ultimo quadro de dados recebido
    data = ''

    while True:
        # espera até o recebimento de um SOF
        sof = con.recv(2)
        if sof.decode() != SOF:
            continue
        
        id = con.recv(2)
        d_rcv.id = int(id.decode(), base=16)

        flags = con.recv(2)
        d_rcv.flags = int(flags.decode(), base=16)

        checksum_rcv = con.recv(4)
        checksum_rcv = int(checksum_rcv.decode(), base=16)

        try:
            if (flags == DATA):
                aux = con.recv(2)
                data += aux 
                while (aux):
                    if(aux == DLE): # Se houver um escape, pegue o próximo como dado
                        aux = con.recv(2)
                        data += aux
                        aux = con.recv(2)
                        continue

                    if(aux.decode16() == EOF): # fim de arquivo (sem escape antes)
                        break
                
                    # caso o byte lido não seja EOF nem DLE
                    aux = con.recv(2)
                    data += aux
                    aux = con.recv(2)

                d_rcv.decode16(data) # todos os dados recebidos 

        except binascii.Error or UnicodeDecodeError:
            print('Erro de conversão!')
            continue

        # verificando se o checksum está correto
        if d_rcv.checksum() != checksum_rcv:
            print('Erro no Checksum!')
            continue

        # 128 = ACK em decimal
        if d_rcv.flags == 128:
            if d_rcv.id == d_send.id:
                print('ACK recebido!')
                d_send.confirmed = True
        else:
            # Se não for ACK, então é dados
            expected_id = 1 if id == 0 else 0
            if d_rcv.id != expected_id:
                print('Retransmitindo dados e reenviando ACK.')
                d_rcv.data = b''
                d_rcv.flags = 128

                con.send(SOF.encode())
                con.send(d_rcv.get_frame())
                continue

            with open(file_name, 'ab') as file:
                file.write(original_data)
                print('Output em: {}\nEnviando ACK.'.format(file_name))
                d_rcv.data = b''
                d_rcv.flags = 128
                id = d_rcv.id

                con.send(SOF.encode())
                con.send(d_rcv.get_frame())


# main: recebe parametros
def main():
    if sys.argv[1] == '-s':
        init_server()
    elif sys.argv[1] == '-c':
        init_client()

    return

if __name__ == '__main__':
    main()