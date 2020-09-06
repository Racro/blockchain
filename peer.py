from node import Peer_Node

ip = input("enter IP")
port = int(input("enter port"))

peer_interval = 10

node = Peer_Node(ip, port)
node.start()

for i in range(10):
	node.sendall(msg)
	time.sleep(peer_interval)

time.sleep(10)