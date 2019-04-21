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

MAX_DATA = 4096 # 512 bytes
SOF = '0xcc'
EOF = '0xcd'
DLE = '0x1b'
ACK = '0x80'
DATA = '0x7f'

class Data:
    def __init__(self, data='', id=1, flags=0):
        self.data = data
        self.confirmed = False
        self.id = id
        self.flags = flags

    def prepare_for_new_data(self):
        self.confirmed = False
        self.id = 1 if self.id == 0 else 0

    @staticmethod
    def _format_numbers(number, is_2_bytes=True):
        pattern = '{:04x}' if is_2_bytes else '{:02x}'
        return pattern.format(number)

    def checksum(self):
        data = 2 * SYNC
        data += self._format_numbers(len(self.data))
        data += self._format_numbers(0)
        data += self._format_numbers(self.id, False)
        data += self._format_numbers(self.flags, False)
        data = binascii.unhexlify(data.encode()) + self.data

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
    def encode16(self):
        return binascii.hexlify(self.data)

    # decrypt
    def decode16(self, new_data):
        self.data = binascii.unhexlify(new_data)

    def get_frame(self):
        formatted_length = self._format_numbers(len(self.data))
        formatted_checksum = self._format_numbers(self.checksum())
        formatted_id = self._format_numbers(self.id, False)
        formatted_flags = self._format_numbers(self.flags, False)
        encoded_data = self.encode16()
        header = (formatted_length + formatted_checksum + formatted_id + formatted_flags).encode()
        return header + encoded_data


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
def initialize_client():
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
    # Timeout de 1s para envio na conexão
    connection.setsockopt(socket.SOL_SOCKET, socket.SO_SNDTIMEO, struct.pack('LL', 10, 0)) 
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
        s.listen()
        connection, addr = s.accept()
        # Timeout de 1s para recebimento na conexão
        s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, struct.pack('LL', 10, 0))
    
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
    with open(file_name, 'rb') as file:
        line = file.read(MAX_DATA) # lê os 512 bytes maximos

        while line:
            d_send.data = line

            con.send(SOF.encode16())
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
                    d_send.prepare_for_new_data()
                    break


def receive_data(con, file_name):
    id = 1 # id do ultimo quadro de dados recebido
    data = ''
    bef = ''
    loop = 0

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
            while (loop == 0):
                aux = con.recv(2)
                data += aux
                while (aux.decode(), base=16) != EOF:
                    bef = aux
                    aux = con.recv(2) 
                    data += aux
                
                if(aux.decode(), base=16) == EOF:
                    if (bef != DLE) # fim de frame
                        loop = 1
            d_rcv.decode16(data)
        except binascii.Error or UnicodeDecodeError:
            print('Erro de conversão!')
            continue

        # verificando se o checksum está correto
        if d_rcv.checksum() != checksum_rcv:
            print('Erro no Checksum!')
            continue

        if d_rcv.flags == 128:
            # treat received ACK
            if d_rcv.id == d_send.id:
                # print('ACK recebido!')
                d_send.confirmed = True
        else:
            # treat new data
            expected_id = 1 if id == 0 else 0
            if d_rcv.id != expected_id:
                # print('Retransmitindo dados e reenviando ACK.')
                d_rcv.data = b''
                d_rcv.flags = 128

                con.send(SOF.encode())
                con.send(d_rcv.get_frame())
                continue

            with open(file_name, 'ab') as file:
                file.write(d_rcv.data)
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