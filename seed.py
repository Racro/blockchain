from node import Seed_Node, get_config

seed_info = get_config(filename)

for i in seed_info:
	seed_node = Seed_Node(i.split(":")[0], int(i.split(":")[1]))
	seed_node.start()

