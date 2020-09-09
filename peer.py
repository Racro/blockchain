from node import Peer_Node
import argparse

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('--adlist',default="127.0.0.1:2000,127.0.0.1:2001",  type=str, help='List of adress - ip1:port1,ip2:port2..')
	parser.add_argument('--msglist',default="Gossip1,Gossip2",  type=str, help='List of gossip messages - msg1,msg2..')
	args = parser.parse_args()

	address_list = args.adlist.split(",")
	message_list = args.msglist.split(",")
	assert len(address_list) == len(message_list)
	num_peer = len(address_list)

	peerList = []
	for i in range(num_peer):
		ip,port = address_list[i].split(":")
		name = "Peer-"+ port
		file = open(name+".txt",'w')
		file.close()
		peerNode = Peer_Node(ip, port, message_list[i], name)
		peerNode.start()
		peerList.append(peerNode)

	for thread in peerList:
		thread.join()

if __name__ == "__main__":
	main()
