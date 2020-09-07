from node import Seed_Node, get_config
filename = "config.txt"

seed_info = get_config(filename)
seed_list = []

# print(seed_info)
count=0
for i in seed_info:
	# print(i)
	seed_node = Seed_Node(i.split(":")[0], int(i.split(":")[1]), name="Seed "+str(count))
	seed_node.start()
	count+=1
	
for t in seed_list:
	t.join()
