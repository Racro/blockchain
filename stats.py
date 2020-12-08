import os
import argparse
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser()
parser.add_argument('--dir',default=".",  type=str, help='Directory for log')

args = parser.parse_args()

dirs = []
names1 = ["run_2sec_20","run_5sec_20","run_10sec_20"]
names2 = ["run_2sec_10","run_5sec_10","run_10sec_10"]
names3 = ["run_2sec_7","run_5sec_7","run_10sec_7"]
percentages = ["10%","20%","30%"]

dirs.append(names1)
dirs.append(names2)
dirs.append(names3)

dirs = [[os.path.join(args.dir,a) for a in names_i] for names_i in dirs]
write_file = "op.txt"

total_nodes_global = []
adv_nodes_global = []
longest_chain_global = []

i=0
for dl in dirs:
	cpl = []
	for d in dl:
		l = []
		pathlist = Path(d).glob('**/*.txt')
		for path in pathlist:
			# fp = os.path.join(directory, filename)
			with open(path,'r') as f:
				# print(path)
				if str(path).split("/")[-1][0] == "S" or str(path).split("/")[-1][0] == "o":
					continue
				# print(path)
				lines = f.read().splitlines()
				last_line = lines[-1]
				if last_line.split(" ")[0] == "Nodes":
					lcom = last_line.split(",")
					st = [d.split(":")[-1] for d in lcom]
					# if len(st) == 5:''
					# 	print(st,len(st))
					st = [float(e) for e in st]
					l.append(st)


		ar = np.asarray(l)
		# print(ar)
		avg = np.average(ar,axis=0)
		wp = os.path.join(d,write_file)
		with open(wp,'w') as file:
			file.write(str(avg))
		cpl.append(avg)
	cpl = np.asarray(cpl)

	total_nodes = cpl[:,0]
	adv_nodes = cpl[:,-1]
	longest_chain = cpl[:,1]

	longest_chain_global.append(longest_chain)
	total_nodes_global.append(total_nodes)
	adv_nodes_global.append(adv_nodes)

	int_time = [2,5,10]

	plt.xlabel("inter-arrival-time")
	plt.ylabel("mining-power-utilisation")
	plt.title("Mining power utilization Vs inter-arrival times for " + percentages[i])	
	plt.plot(int_time,longest_chain/total_nodes)
	plt.savefig("mining-power-utilisation-"+percentages[i]+".jpg")
	plt.clf()

	plt.xlabel("inter-arrival-time")
	plt.ylabel("adversary fraction")
	plt.title("adversary fraction Vs inter-arrival times for " + percentages[i])
	plt.plot(int_time,adv_nodes/longest_chain)
	plt.savefig("adversary-fraction"+percentages[i]+".jpg")
	plt.clf()
	
	i+=1



plt.xlabel("inter-arrival-time")
plt.ylabel("mining-power-utilisation")
plt.title("Mining power utilization comparision")	
p1,=plt.plot(int_time,longest_chain_global[0]/total_nodes_global[0],label="10% flooding")
p2,=plt.plot(int_time,longest_chain_global[1]/total_nodes_global[1],label="20% flooding")
p3,=plt.plot(int_time,longest_chain_global[2]/total_nodes_global[2],label="30% flooding")

plt.legend(handles=[p1,p2,p3])
plt.savefig("Mining-power-comparision"+".jpg")
plt.clf()



plt.xlabel("inter-arrival-time")
plt.ylabel("adversary-fraction")
plt.title("adversary-fraction comparision")	
p1,=plt.plot(int_time,adv_nodes_global[0]/longest_chain_global[0],label="10% flooding")
p2,=plt.plot(int_time,adv_nodes_global[1]/longest_chain_global[1],label="20% flooding")
p3,=plt.plot(int_time,adv_nodes_global[2]/longest_chain_global[2],label="30% flooding")

plt.legend(handles=[p1,p2,p3])
plt.savefig("adversary-fraction-comparision"+".jpg")
plt.clf()