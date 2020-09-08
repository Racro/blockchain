from datetime import datetime
from node import Peer_Node
import argparse

ip = "127.0.0.1"

parser = argparse.ArgumentParser()
parser.add_argument('--port_list',  type=str, help='Port list')
parser.add_argument('--msg_list',  type=str, help='Port list')

parser.add_argument('--sum', dest='accumulate', action='store_const',
                    const=sum, default=max,
                    help='sum the integers (default: find the max)')

message = "Hello"

port = int(input("port: "))

peer_interval = 5 
num_peer = 1
peer_list=[]


for i in range(num_peer):
	print(i)

	file = open("Peer"+str(i)+".txt",'w')
	file.close()

	node = Peer_Node(ip, port, message + str(i), "Peer"+str(i))
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