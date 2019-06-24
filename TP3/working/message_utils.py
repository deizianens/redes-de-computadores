#!/usr/bin/env python3

###########################################
#               Redes - TP3               #
#            message_utils.py             #
#                                         # 
# Autor: Jonatas Cavalcante               #
# Matricula: 2014004301                   #
###########################################

import struct

ID_MSG_TYPE = 4
KEYREQ_MSG_TYPE = 5
TOPOREQ_MSG_TYPE = 6
KEYFLOOD_MSG_TYPE = 7
TOPOFLOOD_MSG_TYPE = 8
RESP_MSG_TYPE = 9
LOCALHOST = '127.0.0.1'


#+---- 2 ---+--- 2 ---------------------------+
#| TIPO = 4 |  PORTO (ou zero se for servent) |
#+----------+---------------------------------+
def create_id_msg(port):
	type = struct.pack("!H", ID_MSG_TYPE)
	port = struct.pack("!H", port)

	msg = type + port

	return msg


#+---- 2 ---+-- 4 -+--- 2 ---+---------------------------+
#| TIPO = 5 | NSEQ | TAMANHO | CHAVE (ate 400 carateres) | 
#+----------+------+---------+---------------------------+
def create_keyreq_msg(nseq, key):
	type = struct.pack("!H", KEYREQ_MSG_TYPE)
	nseq = struct.pack("!I", nseq)
	size = struct.pack("@H", len(key))

	msg = type + nseq + size + key.encode('ascii')

	return msg


#+---- 2 ---+-- 4 -+
#| TIPO = 6 | NSEQ |
#+----------+------+
def create_toporeq_msg(nseq):
	type = struct.pack("!H", TOPOREQ_MSG_TYPE)
	nseq = struct.pack("!I", nseq)

	msg = type + nseq

	return msg


#+---- 2 ------+- 2 -+-- 4 -+--- 4 ---+----- 2 ----+--- 2 ---+--------------------------+ 
#| TIPO = 7, 8 | TTL | NSEQ | IP_ORIG | PORTO_ORIG | TAMANHO | INFO (ate 400 carateres) | 
#+-------------+-----+------+---------+------------+---------+--------------------------+
def create_flood_message(msg_type, ttl, nseq, src_port, info):
	
	if msg_type == KEYFLOOD_MSG_TYPE:
		type = struct.pack("!H", KEYFLOOD_MSG_TYPE)
	else:
		type = struct.pack("!H", TOPOFLOOD_MSG_TYPE)

	ttl = struct.pack("!H", ttl)
	nseq = struct.pack("!I", nseq)
	src_ip = LOCALHOST.split(".")
	msg = type + ttl + nseq

	for i in range(0,4):
		msg += struct.pack("!b", int(src_ip[i]))

	src_port = struct.pack("!H", src_port)
	size = struct.pack("@H", len(info))
	msg += src_port + size + info.encode('ascii')

	return msg


#+---- 2 ---+-- 4 -+--- 2 ---+---------------------------+ 
#| TIPO = 9 | NSEQ | TAMANHO | VALOR (ate 400 carateres) | 
#+----------+------+---------+---------------------------+
def create_resp_msg(nseq, value):
	type = struct.pack("!H", RESP_MSG_TYPE)
	nseq = struct.pack("!I", nseq)
	size = struct.pack("@H", len(value))

	msg = type + nseq + size + value.encode('ascii')

	return msg


def receive_servent_msg(con, nseq):
	msg_type = struct.unpack("!H", con.recv(2))[0]
	msg_nseq = struct.unpack("!I", con.recv(4))[0]

	(src_ip, src_port) = con.getpeername()

	if msg_type != 9 or msg_nseq != nseq:
		print("Mensagem incorreta recebida de " + str(src_ip) + ":" + str(src_port))
	else:
		msg_size = struct.unpack("@H", con.recv(2))[0]
		msg_value = con.recv(msg_size)
		print(msg_value.decode('ascii') + " " + str(src_ip) + ":" + str(src_port))


def get_keyreq_msg_data(con):
	nseq = struct.unpack("!I", con.recv(4))[0]
	size = struct.unpack("@H", con.recv(2))[0]
	key = con.recv(size)

	return nseq, key.decode('ascii')


def get_toporeq_msg_data(con):
	nseq = struct.unpack("!I", con.recv(4))[0]

	return nseq


def get_flood_msg_data(con):
	ttl = struct.unpack("!H", con.recv(2))[0]
	nseq = struct.unpack("!I", con.recv(4))[0]

	# for i in range(0,4):
	# 	src_ip += struct.unpack("!b", con.recv(1))[0]
	# 	if i < 3:
	# 		src_ip += '.'

	src_ip_1 = struct.unpack("!b", con.recv(1))[0]
	src_ip_2 = struct.unpack("!b", con.recv(1))[0]
	src_ip_3 = struct.unpack("!b", con.recv(1))[0]
	src_ip_4 = struct.unpack("!b", con.recv(1))[0]

	src_port = struct.unpack("!H", con.recv(2))[0]
	size = struct.unpack("@H", con.recv(2))[0]
	info = con.recv(size)

	return ttl, nseq, LOCALHOST, src_port, info.decode('ascii')