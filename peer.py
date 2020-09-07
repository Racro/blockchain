from datetime import datetime
from node import Peer_Node

ip = "127.0.0.1"
port = int(input("enter port"))
message = "Hello"

peer_interval = 5

node = Peer_Node(ip, port,"Peer")
node.start()
node.join()
exit(0)

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