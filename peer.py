from node import Peer_Node
import argparse

def peer_gen():
	parser = argparse.ArgumentParser()
	parser.add_argument('--adlist',default="127.0.0.1:2000,127.0.0.1:2001",  type=str, help='List of adress - ip1:port1,ip2:port2..')
	parser.add_argument('--msglist',default="Gossip,Hello",  type=str, help='List of gossip messages - msg1,msg2..')
	parser.add_argument('--hashPower',default="50,50",  type=str, help='List of hasing power for peers - p1,p2..')
	parser.add_argument('--time',default=2,  type=float, help='Inter arrival time')
	parser.add_argument('--is_adversary',default=False, help='Is node an adversary', action="store_true")
	parser.add_argument('--simulate',default=False, help='Is simulation for graphs of assignment', action="store_true")
	parser.add_argument('--draw_tree',default=False, help='Display graph for node', action="store_true")
	parser.add_argument('--num',default=0,  type=int, help='Number of nodes')

	
	args = parser.parse_args()

	if args.simulate:
		address_list = ["127.0.0.1:"+str(n) for n in range(2000,2000+args.num)]
		message_list=["gossip"]*args.num
		hashing_list = [(100-33)/args.num]*args.num
	else:
		address_list = args.adlist.split(",")
		# message_list = args.msglist.split(",")
		message_list=["gossip"]*len(address_list)
		hashing_list = args.hashPower.split(",")
		assert len(address_list) == len(hashing_list)
	num_peer = len(address_list)

	peerList = []
	for i in range(num_peer):
		ip,port = address_list[i].split(":")
		name = "Peer-"+ port
		file = open(name+".txt",'w')
		file.close()

		peerNode = Peer_Node(ip, port, message_list[i], name,float(hashing_list[i]),args.is_adversary,args.time,draw_tree=args.draw_tree)
		peerNode.start()
		peerList.append(peerNode)

	for thread in peerList:
		thread.join()

if __name__ == "__main__":
	peer_gen()
