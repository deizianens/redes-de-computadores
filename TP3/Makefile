client1:
	python3 TP3client.py 55555 127.0.0.1:55555

client2:
	python3 TP3client.py 55501 127.0.0.1:55557

servent1:
	python3 TP3node.py 55555 ./test/keyTest1.txt [127.0.0.1:55554]

servent2:
	python3 TP3node.py 55554 ./test/keyTest2.txt [127.0.0.1:55555[127.0.0.1:55556[127.0.0.1:55557]]]

servent3:
	python3 TP3node.py 55556 ./test/keyTest3.txt [127.0.0.1:55554[127.0.0.1:55558]]

servent4:
	python3 TP3node.py 55557 ./test/keyTest4.txt [127.0.0.1:55554[127.0.0.1:55558]]

servent5:
	python3 TP3node.py 55558 ./test/keyTest.txt [127.0.0.1:55556[127.0.0.1:55559][127.0.0.1:55557]]

servent6:
	python3 TP3node.py 55559 ./test/keyTest.txt [127.0.0.1:55558[127.0.0.1:55560]]

servent7:
	python3 TP3node.py 55560 ./test/keyTest.txt [127.0.0.1:55559]

servent8:
	python3 TP3node.py 55561 ./test/keyTest.txt [127.0.0.1:55560]