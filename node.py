import random
import threading
from datetime import datetime
import socket
import time
import hashlib
import random
import math
import ast
import numpy

filename = "config.csv"
MAXBUF = 1024
h = hashlib.sha3_256() 


genesis_hash = "9e1c"

class Seed_Node (threading.Thread):
	def __init__(self, ip, port, name=""):

		threading.Thread.__init__(self)
		self.ip = ip
		self.name = name
		self.port = port
		self.addr = (ip,port)
		self.client_list = []
		self.file = name + ".txt"
		# self.client_conn = []
		self.peer_threads = []
		self.stop_server = threading.Event()
		self.init_seed_server()

	def init_seed_server(self):
		self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP echo socket
		self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.server_sock.bind((self.ip, self.port))		# Bind to the port
		# self.server_sock.settimeout(10.0)
		self.server_sock.listen()				 # Now wait for client connection (max 5 clients)

	def run(self):
		print ("Starting " + self.name)
		while not self.stop_server.is_set():
			try:
				conn, incoming_addr = self.server_sock.accept()
				# print(self.name + " received connection from: ", incoming_addr)

				try:
					msg = self.recv_msg(conn)

					# print(msg)
					if msg.split(":")[0] == "Register":
						incoming_addr = (str(msg.split(":")[1]),int(msg.split(":")[2])) #strored as tuple
						write_to_terminal(msg)
						write_to_file(self.file, msg)
						
						# print(incoming_addr)
						msg = ""
						for i in self.client_list:
							msg = msg + i[0] + ":" + str(i[1]) + " "
						msg = form_clientList_msg(msg, self.addr)
						# print(msg)
						# print("$"*50)
						self.send_msg(msg,incoming_addr)

						if incoming_addr not in self.client_list:
							self.client_list.append(incoming_addr)


					elif msg.split(":")[0] == "Dead Node":
						incoming_addr = msg.split(":")[1] + ":" + msg.split(":")[2]
						if incoming_addr in self.client_list:
							self.client_list.remove(incoming_addr)
						write_to_terminal(msg)
						write_to_file(self.file, msg)
				except socket.timeout:
					error("timeout in seed recv")
					pass

				except Exception as e:
					error(e)
			except socket.timeout:
				error("timeout in seed accept")
				pass

			except Exception as e:
				error(e)
				self.stop_server.set()
		self.server_sock.close()

	def send_msg(self, msg,addr):
		# print("preparing to sned peer info",msg,addr)

		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
			s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			s.connect(addr)
			s.sendall(msg.encode('utf-8'))	

	def recv_msg(self, sock):
		msg = ""
		while True:
			data = sock.recv(MAXBUF)
			if not data: 
				break
			# print(repr(data))
			msg+=data.decode('utf-8')
		
		return msg

class Peer_Node (threading.Thread):
	def __init__(self, ip, port, message, name, hashPower, is_adversary,inter_arrival_time=10,iter=0,draw_tree=False):
		threading.Thread.__init__(self)
		self.ip = ip
		self.name = name
		self.port = int(port)
		self.addr = ip + ":" + str(port)
		self.is_adversary = is_adversary
		self.draw_tree = draw_tree

		self.inter_arrival = inter_arrival_time
		self.global_lambda = 1/inter_arrival_time
		
		#self.MAXBUF = 1024
		self.database = {}
		self.database[0] = [([genesis_hash, 0, 0],-1,0)]
		self.cur_length = 1
		self.hashPower = hashPower
		self.lamb = (self.hashPower * self.global_lambda)/100
		
		self.pending_queue = []

		self.message = message
		self.peer_info = []
		self.seed_info = []
		self.iter=iter
		
		self.file = name+".txt"
		self.lock = threading.Lock()
		self.pending_lock = threading.Lock()
		self.stop_server = threading.Event()
		self.liveliness_count = {}
		self.ML = {}

		self.peer_threads = []
		#self.conn_to_ip = {}
		self.make_socket()

		self.broadcast_dict={}

	def make_socket(self):
		
		# print(self.ip,self.port)
		self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP echo socket
		self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.server_sock.bind((self.ip, self.port))		# Bind to the port
		# self.server_sock.settimeout(10.0)
		self.server_sock.listen()				 # Now wait for client connection (max 5 clients)

		#write to file and register node
		self.register_with_seed()
		self.register_with_peer()
		self.spawn_communication_threads()
		

	def register_with_seed(self):
		seed_info = get_config(filename)
		seed_size = len(seed_info)
		if (seed_size==0):
			error() #return seed empty
		else:
			reg_size = int(seed_size/2) + 1
			reg_list = random.sample(seed_info, reg_size)
		self.seed_info = reg_list
		# print("Seed info for:", self.name, repr(self.seed_info))

		client_union = []		
		for i in reg_list:
			ip = i.split(":")[0]
			port = int(i.split(":")[1])
			reg_msg = form_reg_msg(str(self.ip) + ":" + str(self.port))
			addr=(ip,int(port))
			self.send_msg(reg_msg,addr)
			
			#Now receive existing peer data on listner port named server sock
			conn, addr = self.server_sock.accept()
			# print("here")
			
			client_list = self.recv_msg(conn)
			if (client_list.split("-")[0]=="ClientList"):
				write_to_terminal(client_list)
				write_to_file(self.file, client_list)
				client_list = client_list.split("-")[2]
			else:
				error("wrong clientList")
			client_union = Union(client_union, client_list.split(" "))
				
		# print("Number of peers returned:",len(client_union))	
		# print(client_union)
		self.peer_info = random.sample(client_union, min(2,len(client_union)))
		print(self.peer_info)

	def register_with_peer(self):
		Bk = []
		conn_list = []
		for i in self.peer_info:
			ip,port = i.split(":")[0],int(i.split(":")[1])
			if (ip==self.ip and port==self.port):
				self.peer_info.remove(i)
				error("can't connect to same ip/port")
				continue

			#Now send self adress to the old established peer
			addr = (ip,port)
			reg_msg = form_reg_msg(str(self.ip) + ":" + str(self.port))
			self.send_msg(reg_msg,addr)

			# print("reg/msg sent by",self.name)
			if i not in self.liveliness_count.keys():
				self.liveliness_count[i] = 0

			#receiving Bk node
			while(True):
				conn, incoming_addr = self.server_sock.accept()
				# print("wait sent by",self.name)

				msg = self.recv_msg(conn)
				# print("Stuck")
				# print(msg)

				if self.Bk_req(msg):
					# print("yoohoo")
					Bk.append((ast.literal_eval(msg.split(":")[1]), int(msg.split(":")[2])))
					conn_list.append((msg.split(":")[-2], int(msg.split(":")[-1])))
					break
				elif msg=="":
					print("No blocks in bkc yet")
					break

		if len(Bk) == 0:
			return
		print(Bk)
		# exit(0)

		latest_time = Bk[0][0][2]
		blk = Bk[0]
		con = conn_list[0]
		for i in range(1, len(Bk)):
			if(Bk[i][0][2] > latest_time):
				latest_time = Bk[i][0][2]
				blk = Bk[i]
				con = conn_list[i]
		self.pending_lock.acquire()
		self.pending_queue.append((blk[0], con))  #need to find k and trim blk to block header
		self.pending_lock.release()
		reply = form_0_k_req((blk[0], blk[1]), self.addr) #need to add other relevant info 
		addr = con
		self.send_msg(reply, addr)

	def spawn_communication_threads(self):
		#start gossip - no gossip rn
		# peer_gossip_thread = PeerConnection(self,0)
		# peer_gossip_thread.start()
		# self.peer_threads.append(peer_gossip_thread)		
		if not self.is_adversary:
			# start liveliness
			# peer_liveliness_thread = PeerConnection(self,1)
			# peer_liveliness_thread.start()
			# self.peer_threads.append(peer_liveliness_thread)		

			#Setup for new node must be complete at this point

			print("start mining thread")
			#Start Honest Node Mining process
			peer_mining_thread = PeerConnection(self,2)
			peer_mining_thread.start()
			self.peer_threads.append(peer_mining_thread)		

		else:
			# start liveliness
			# peer_liveliness_thread = PeerConnection(self,1)
			# peer_liveliness_thread.start()
			# self.peer_threads.append(peer_liveliness_thread)		

			#Setup for new node must be complete at this point

			#Start Honest Node Mining process
			peer_mining_thread = PeerConnection(self,2)
			peer_mining_thread.start()
			#adversarial random block generation
			adversary_thread = PeerConnection(self,3)
			adversary_thread.start()

			self.peer_threads.append(peer_mining_thread)
			self.peer_threads.append(adversary_thread)		



	def run(self):
		print ("Starting Peer: " + self.name)
		
		while not self.stop_server.is_set():
			try:
				conn, incoming_addr = self.server_sock.accept()
				try:
					msg = self.recv_msg(conn)

					# print("MESSAGE RECIEVED:",msg,"by",self.name)

					if self.register_msg(msg):
						addr = msg.split(":")[1]+":"+msg.split(":")[2]
						if addr not in self.peer_info:
							self.peer_info.append(addr)
						k = len(self.database.keys()) - 1
						if (k > 0):
							reply = form_Bk_msg(self.database[k], k, self.addr)
						else:
							reply = ""
						addr = (msg.split(":")[1], int(msg.split(":")[2]))
						self.send_msg(reply, addr)


					elif self.liveliness_req(msg):
						#reply 
						reply = form_liveliness_reply(msg.split(":")[1], msg.split(":")[2], self.addr)
						addr = (msg.split(":")[2], int(msg.split(":")[3]))
						self.send_msg(reply, addr)

					elif self.liveliness_reply(msg):
						#reply
						self.liveliness_count[msg.split(":")[3]+":"+msg.split(":")[4]] = 0

					elif self.gossip(msg):
						#reply
						# print("Goo")
						message = msg.split(":")[0]+":"+msg.split(":")[1]+":"+msg.split(":")[2]+":"+msg.split(":")[3]
						incoming_addr = msg.split(":")[-2] + ":" + msg.split(":")[-1]
						md5 = hashlib.md5(message.encode()).hexdigest()
						# self.server.lock.acquire()
						if md5 not in self.ML.keys():
							self.ML[md5] = True
							print_msg = str(datetime.now()) + ":" + incoming_addr + ":" + message.split(":")[3] 
							write_to_terminal(print_msg)
							write_to_file(self.file, print_msg)
							#write to file
							#check for exclusion of address from where recieved gossip msg
							
							exclude = []
							exclude.append(incoming_addr)
							msg = form_gossip_msg(self.addr, message, 1)
							self.broadcast(msg, exclude)

						# self.server.lock.release()
					elif self.B0_Bk_req(msg): #msg will have last entry as k(height) and second last entry as kth block
						blk = ast.literal_eval(msg.split(":")[1])
						K_blk = blk[0]
						k = blk[1]
						prev_hash = K_blk[0]
						send_lst = []
						for i in range(k-1,-1,-1):
							for j in self.database[i]:
								hsh = sha3[j[0]]
								if(hsh == prev_hash):
									prev_hash = hsh
									send_lst.append(j)
									break
						addr = (msg.split(":")[-2], int(msg.split(":")[-1]))
						reply = form_0_k_reply( send_lst, self.addr) 
						self.send_msg(reply, addr) 
					
					elif self.B0_Bk_reply(msg): #lst entry being the lst
						lst = ast.literal_eval(msg.split(":")[1])
						for i in range(len(lst), -1, -1):
							self.database[i] = lst[i]
					
					elif self.block_msg(msg):
						# print("Recieved block********************")
						blk = ast.literal_eval(msg.split(":")[1])
						incoming_addr = msg.split(":")[-2] + ":" + msg.split(":")[-1]
						#acquire_lock for pending queue
						self.pending_lock.acquire()
						exists=False
						for item in self.pending_queue:
							if item[0] == blk:
								exists=True
								break
						if not exists:
							self.pending_queue.append((blk, incoming_addr))
						self.pending_lock.release()

					else:
						error("invalid format")
						
				except socket.timeout:
					error("timeout in peer recv")

				except Exception as e:
					error(e)
			except socket.timeout:
				error("timeout in peer accept")
			
			except Exception as e:
				error(e)
				for i in peer_threads:
					i.join()
				self.stop_server.set()
		self.server_sock.close()
	

	def send_msg(self, msg,addr):
		try:
			# self.lock.acquire()
			with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
				s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				s.connect(addr)
				s.sendall(msg.encode('utf-8'))
			s.close()
			# self.lock.release()
		except Exception as e:
			# self.lock.release()
			error(e)
			
	def recv_msg(self, sock, lock=None):
		msg = ""

		while True:
			data = sock.recv(MAXBUF)
			if not data: 
				break
			msg = msg + data.decode('utf-8')
		return msg

	def broadcast (self, msg, exclude=[]):
		for i in self.peer_info:
			if i not in exclude:
				addr = (i.split(":")[0], int(i.split(":")[1]))
				self.send_msg(msg,addr)
		print("Broadcast complete")
		
	def register_msg(self, msg):

		# print(msg)
		if msg.split(":")[0] == "Register":
			return True
		else:
			# print("Failed")
			return False

	def liveliness_req(self, msg):
		if (msg.split(":")[0] == "Alive?"):
			return True
		else:
			return False

	def liveliness_reply(self, msg):
		if (msg.split(":")[0] == "Yes, Alive"):
			return True
		else:
			return False

	def gossip(self, msg):
		check=0
		try:	
			time = datetime.strptime(msg.split(":")[0], '%d-%m-%Y-%H-%M-%S')
			check=1
		except:
			pass
	
		return check
	
	def B0_Bk_reply(self, msg):
		if(msg.split(":")[0] == "0_k_reply"):
			return 1
		else:
			return 0

	def B0_Bk_req(self, msg):
		if(msg.split(":")[0] == "0_k_req"):
			return 1
		else:
			return 0

	def Bk_req(self, msg):
		if (msg.split(":")[0] == "Bk_req"):
			return 1
		else:
			return 0
	
	def block_msg(self, msg):
		if (msg.split(":")[0] == "block_msg"):
			return 1
		else:
			return 0
			
	def longest_chain_stats(self):
		count_total_nodes = 0
		parent_index = 0
		longest_chain = []
		my_nodes = 0
		count_adv_nodes=0
		
		for i in range(self.cur_length-1,-1,-1):
			if (self.database[i][parent_index][2] == 1):
				my_nodes+=1
			if (self.database[i][parent_index][0][1] == "ffff"):
				count_adv_nodes+=1

			longest_chain.append(self.database[i][parent_index])
			parent_index = self.database[i][parent_index][1]
			count_total_nodes += len(self.database[i])

		return [count_total_nodes, my_nodes, len(self.database), count_adv_nodes]	
	
	def validate(self,block):
		for height,bil in self.database.items():
			for i in range(len(bil)):
				# print(bil,"vali")
				bt = bil[i]
				# print(bt[0])

				# h.update(str(bt[0]).encode())
				hsh = sha3(bt[0])
				# print(hsh)
				# print(block)
				# print("error?")
				if (block[0] == hsh):
					return[height,i]

		return [-1,-1]

	def construct_tree(self):
		print("Here")
		num_tabs = 1
		print('\t'*num_tabs)
		max_level = self.cur_length-1
		for i in range(max_level):
			bfl = self.database[i]
			print("\t"*num_tabs,str(i)+":",end="")
			num_tabs+=1
			i=0
			for bi in bfl:
				print("\t"*(num_tabs+i),bi[0],"parent index:", bi[1])
				if i==0:
					i+=1
				
			num_tabs-=1
					


class PeerConnection (threading.Thread):
	def __init__(self, server, flag):
		threading.Thread.__init__(self)
		self.addr = server.ip+":"+str(server.port)
		self.server = server
		self.flag = flag
		self.stop_server = threading.Event()
		
		self.gossip_interval = 5
		self.liveliness_interval = 13


	def run(self):
		
		if self.flag == 0:
			for i in range(10):
				msg = form_gossip_msg(self.addr, self.server.message + str(i), 0)
				self.broadcast(msg)					
				time.sleep(self.gossip_interval)

		elif self.flag == 1:
			while True:
				msg = form_liveliness_req(self.server.addr)
				self.broadcast(msg)
				time.sleep(self.liveliness_interval)
				self.check_liveliness()
								
		elif self.flag == 2:
			self.begin = time.time()
			timeout = self.begin + 60*5
			# Mining Thread
			while time.time() < timeout:
				# print("Mining Started")
				# print(self.server.database[self.server.cur_length-1][0][0])
				# h.update(str(self.server.database[self.server.cur_length-1][0][0]).encode())
				hsh = sha3(self.server.database[self.server.cur_length-1][0][0])
				# print("new-prev",hsh)
				block=gen_block_header(hsh)
				waitingTime = numpy.random.exponential(1/self.server.lamb)
				time.sleep(max(waitingTime,0))
				statement = "Sleep of "+str(max(waitingTime,0))+" By:"+self.server.name+" Time:"+str((time.time()-self.begin)/60)
				# print("Sleep of",waitingTime,"completed", self.server.name, "time:",str(time.time()-begin)/60)
				write_to_terminal(statement)
				write_to_file(self.server.file,statement)

				self.mining_process(block)
				print("Mining Cycle completed. Time:",(time.time()-self.begin)/60)

			write_to_file(self.server.file,"blockchain stats")
			write_to_terminal("blockchain stats")
			# for key,values in self.server.database.items():
			# 	write_to_file(self.server.file,str(key) + " " + str(len(values)))
			# 	write_to_terminal(str(key) + " " + str(len(values)))
			stats = self.server.longest_chain_stats()
			statement = "Nodes in db:"+str(stats[0])+",longest chain:"+str(stats[2])+",my nodes:"+str(stats[1])+",hashingPower:"+str(self.server.hashPower)+",adv-nodes:"+str(stats[3])
			write_to_file(self.server.file,statement)
			write_to_terminal(statement)
			# print(statement)

			if self.server.draw_tree:
				self.server.construct_tree()

			# print("Done")
		
		elif self.flag == 3:
			#adversary thread
			print("Adversary is now flooding neighbours every 2 second")
			while(True):
				time.sleep(2) #2 is some random
				block=gen_block_header("0"*4)
				blk_msg = form_block_msg(block, self.addr)
				self.broadcast(blk_msg)
		else:
			error("wrong flag")
	
	def mining_process(self,block):
		hsh= sha3(block)
		if len(self.server.pending_queue) == 0:
			if self.server.is_adversary:
				block[1] = "ffff"
			blk_msg = form_block_msg(block, self.addr)
			self.broadcast(blk_msg)
			tup = (block,0,1)
			self.server.database[self.server.cur_length] = [tup]
			hs= sha3(block)
			self.server.broadcast_dict[hs]=1

			statement = "Broadcasted mined block "+str(tup)+" By:"+self.server.name+" Time:"+str((time.time()-self.begin)/60)
			write_to_file(self.server.file,statement)
			write_to_terminal(statement)

			self.server.cur_length+=1
		else:
			if not hsh in self.server.broadcast_dict:
				self.update_database()
				self.server.broadcast_dict[hsh] = 1

	def update_database(self):
		print("Length of pending que is",len(self.server.pending_queue))
		for _ in range(len(self.server.pending_queue)):
			for item in self.server.pending_queue:
				block = item[0]
				addr = item[1]
				[h,i] = self.server.validate(block)
				if h!=-1:
					block_info = (block,i,0)
					blk_msg = form_block_msg(block, self.addr)
					self.broadcast(blk_msg,[addr])

					if h==self.server.cur_length-1:
						self.server.database[self.server.cur_length]= [block_info]
						self.server.cur_length+=1
					else:
						exists=False
						for bi in self.server.database[h+1]:
							if bi[0] == block:
								exists=True
								break
						if not exists:
							self.server.database[h+1].append(block_info)
					self.server.pending_queue.remove(item)
		
		print("Update complete", self.server.name)
		self.server.pending_queue = []

			
	def check_liveliness (self):
			to_remove = []
			for i in self.server.liveliness_count:
				if (self.server.liveliness_count[i] >= 3):

					to_remove.append(i)
					for addr in self.server.seed_info:
						
						ip = addr.split(":")[0]
						port = addr.split(":")[1]
						addr_tup = (ip,int(port))
						self.send_msg(form_deadNode_msg(i, self.addr),addr_tup)
						write_to_terminal(form_deadNode_msg(i, self.addr))
						write_to_file(self.server.file, form_deadNode_msg(i, self.addr))
						
			if len(to_remove) != 0:
				for i in to_remove:
					del self.server.liveliness_count[i]
					self.server.peer_info.remove(i)

			for i in self.server.liveliness_count:
				self.server.liveliness_count[i] += 1

	def send_msg(self, msg,addr):
		try:
			# self.server.lock.acquire()
			with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
				s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				# print("*"*10)
				
				s.connect(addr)
				# print("#"*10)

				s.sendall(msg.encode('utf-8'))
			# self.server.lock.release()
		except Exception as e:
			# self.server.lock.release()
			error(e)

	def broadcast (self, msg, exclude=[]):
		for i in self.server.peer_info:
			if i not in exclude:
				addr = (i.split(":")[0], int(i.split(":")[1]))

				self.send_msg(msg,addr)

			
def get_config(filename):
	with open(filename, "r") as f:
		seed_info=[]
		for line in f:
			seed_info.append(line.strip())
	return seed_info

def Union(lst1, lst2):
	lst2 = [i for i in lst2 if i]
	final_list = list(set(lst1) | set(lst2))
	return final_list 


def form_liveliness_req(ip):
	req = "Alive?"
	t = datetime.now()
	t_str = t.strftime("%d-%m-%Y-%H-%M-%S")
	req = req + ":" + t_str + ":" + ip
	return req

def form_liveliness_reply(t, sender_ip, self_ip):
	req = "Yes, Alive"
	req = req + ":" + str(t) + ":" + sender_ip + ":" + self_ip
	return req

def form_deadNode_msg(addr, self_ip):
	msg = "Dead Node"
	t = datetime.now()
	t_str = t.strftime("%d-%m-%Y-%H-%M-%S")
	msg = msg + ":" + addr + ":" + str(t) + ":" + self_ip
	return msg 

def form_clientList_msg(msg, addr):
	msg = "ClientList-"+str(addr)+"-"+msg
	return msg

def error(msg):
	print(msg)


def form_gossip_msg( self_addr, message, flag):
	if (flag == 0):
		t = datetime.now()
		t_str = t.strftime("%d-%m-%Y-%H-%M-%S")
		msg = t_str + ":" + self_addr + ":" + message + ":" + self_addr
		return msg
	elif (flag == 1):
		msg = message + ":" + self_addr
		return msg
	else:
		error("wrong flag in gossip")


def form_reg_msg(addr):
	msg = "Register:"
	msg = msg + addr
	return msg

def form_0_k_req(blk, addr): #blk = (blk, height)
	msg = "0_k_req"
	msg = msg + ":" + str(blk) + ":" + addr
	return msg
	
def form_0_k_reply(lst, addr):
	msg = "0_k_reply"
	msg = msg + ":" + str(lst) + ":" + addr
	return msg
	
def form_Bk_msg(blk, k, addr):
	msg = "Bk_req"
	msg = msg + ":" + str(blk) + ":" + str(k) + ":" + addr
	return msg

def form_block_msg(blk, addr):
	msg = "block_msg"
	msg = msg + ":" + str(blk) + ":" + addr
	return msg
	
def send_msg( sock, msg):
	try:
		sock.send(msg)
	except Exception as e:
		error(e)
		error("can't send msg")

def write_to_file(file, msg):
	f = open(file, "a+")
	f.write(msg)
	f.write("\n")
	f.close()

def write_to_terminal(msg):
	print(msg)

def gen_block_header(prev_hash):
	# h.update(str(random.random()).encode())
	hsh = sha3(random.random())

	block = [prev_hash, hsh, math.floor(time.time())]
	return block

def sha3(block):
	s = hashlib.sha3_224() 
	s.update(str(block).encode())
	hsh = s.hexdigest()[0:4]
	return hsh 
