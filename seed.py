from node import Seed_Node
import argparse

def getSeedAddr(args):
	addrList=[]
	with open(args.config,'r') as file:
		line_count = 0
		for line in file:
			line = line.strip()
			if (len(line) == 0):
				continue
			if line_count >= args.startline and line_count <= args.endline:
				addrList.append(line)
			line_count+=1
	return addrList

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("startline",type=int,help="Starting line# from config file")
	parser.add_argument("endline",type=int,help="Ending line# from config file")

	args = parser.parse_args()
	args.config = "config.csv"
	
	addrList = getSeedAddr(args) 
	seedList = []

	for addr in addrList:
		ip,port = addr.split(":")
		name = "Seed-"+port
		file = open(name+".txt",'w')
		file.close()
		seedNode = Seed_Node(ip, int(port), name=name)
		seedNode.start()
		seedList.append(seedNode)

	for seed in seedList:
		seed.join()


if __name__ == "__main__":
	main()