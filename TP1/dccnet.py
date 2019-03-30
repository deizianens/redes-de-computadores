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

class Data:
    


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

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((IP, PORT))
    s.listen(1)

    connection = s.accept()[0]

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
        line = file.read(MAX_DATA)

        while line:
            d_send.data = line

            con.send(SYNC.encode())
            con.send(SYNC.encode())
            con.send(d_send.get_frame())
            log('Data sent from file ' + file_name)

            global ack_timeout
            ack_timeout = False

            def handle_timeout():
                global ack_timeout
                ack_timeout = True

            # to measure time
            timer = threading.Timer(1, handle_timeout)
            timer.start()
            while True:
                if ack_timeout:
                    log('ACK not received.')
                    break

                if d_send.confirmed:
                    line = file.read(MAX_DATA)
                    d_send.prepare_for_new_data()
                    break


def receive_data(con, file_name):
    last_received_id = 1

    while True:
        # waiting for data
        # finding SYNC expression
        sync = con.recv(8)
        if sync.decode() != SYNC:
            # resynchronizing
            continue

        sync = con.recv(8)
        if sync.decode() != SYNC:
            # resynchronizing
            continue

        # collecting information in the string
        length = con.recv(4)
        data_to_receive.length = int(length.decode(), base=16)

        received_checksum = con.recv(4)
        received_checksum = int(received_checksum.decode(), base=16)

        id = con.recv(2)
        data_to_receive.id = int(id.decode(), base=16)

        flags = con.recv(2)
        data_to_receive.flags = int(flags.decode(), base=16)

        try:
            data = con.recv(2*data_to_receive.length)
            data_to_receive.decode16(data)
        except binascii.Error or UnicodeDecodeError:
            log('Conversion error!')
            continue

        # verifying checksum value
        if data_to_receive.checksum() != received_checksum:
            log('Checksum error!')
            continue

        if data_to_receive.flags == 128:
            # treat received ACK
            if data_to_receive.id == d.id:
                log('ACK received.')
                d.confirmed = True

        else:
            # treat new data
            expected_id = 1 if last_received_id == 0 else 0
            if data_to_receive.id != expected_id:
                log('Retransmission data, resending ACK.')
                data_to_receive.data = b''
                data_to_receive.flags = 128

                con.send(SYNC.encode())
                con.send(SYNC.encode())
                con.send(data_to_receive.get_frame())
                continue

            with open(file_name, 'ab') as file:
                file.write(data_to_receive.data)
                log('Data written on file {}, sending ACK.'.format(file_name))
                data_to_receive.data = b''
                data_to_receive.flags = 128
                last_received_id = data_to_receive.id

                con.send(SYNC.encode())
                con.send(SYNC.encode())
                con.send(data_to_receive.get_frame())




# main: recebe parametros
def main():
    if sys.argv[1] == '-s':
        init_server()
    elif sys.argv[1] == '-c':
        init_client()

    return

if __name__ == '__main__':
    main()