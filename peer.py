from datetime import datetime
from node import Peer_Node

ip = input("enter IP")
port = int(input("enter port"))
message = input("enter gossip msg")

peer_interval = 5

node = Peer_Node(ip, port)
node.start()

def form_msg(ip, message):
	msg = ""
	t = datetime.now()
	msg = msg + t + ":" + ip + ":" + message
	return msg

for i in range(10):
	msg = form_msg(ip, message)
	node.sendall(msg)
	time.sleep(peer_interval)

time.sleep(10)