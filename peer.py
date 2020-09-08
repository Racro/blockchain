from datetime import datetime
from node import Peer_Node

ip = "127.0.0.1"
port = 2005
message = "Hello"

peer_interval = 5
num_peer = 4
peer_list=[]

for i in range(num_peer):
	print(i)
	node = Peer_Node(ip, port+i,"Peer"+str(i))
	node.start()
	peer_list.append(node)

for thread in peer_list:
	thread.join()
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