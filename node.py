import random
import threading
from datetime import datetime
import socket

filename = "config.txt"
MAXBUF = 1024
#Handle dead nodes
#peer port is not same
class Seed_Node (threading.Thread):
	def __init__(self, ip, port, name=""):

		threading.Thread.__init__(self)
		self.ip = ip
		self.name = name
		self.port = port
		self.client_list = []
		# self.client_conn = []
		self.stop_server = threading.Event()
		self.init_seed_server()

	def init_seed_server(self):
		self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP echo socket
		self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.server_sock.bind((self.ip, self.port))		# Bind to the port
		self.server_sock.settimeout(10.0)
		self.server_sock.listen(5)				 # Now wait for client connection (max 5 clients)

	def run(self):
		print ("Starting " + self.name)
		while not self.stop_server.is_set():
			try:
				conn, incoming_addr = self.server_sock.accept()
				print(self.name + " received con from: ", incoming_addr)

				try:
					msg = self.recv_msg(conn)
					if msg.split(":")[0] == "Peer Data":
						incoming_addr = (str(msg.split(":")[1]),int(msg.split(":")[2])) #strored as tuple
						print("Got From peer ",incoming_addr)
						
						msg = ""
						for i in self.client_list:
							msg = msg + i[0] + ":" + str(i[1]) + " "
						
#############						self.send_info(msg,incoming_addr)

						if incoming_addr not in self.client_list:
							self.client_list.append(incoming_addr)


					elif msg.split(":")[0] == "Dead Node":
						incoming_addr = msg.split(":")[1]
						if incoming_addr in self.client_list:
							self.client_list.remove(incoming_addr)

				except socket.timeout:
					pass

				except Exception as e:
					print("exception in recv")
			except socket.timeout:
				pass

			except Exception as e:
				print(repr(e))
				print("Foo")
				self.stop_server.set()

	def send_info(self, msg,addr):
		# print("preparing to sned peer info",msg,addr)
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
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
	def __init__(self, ip, port, name):
		threading.Thread.__init__(self)
		self.ip = ip
		self.name = name
		self.port = port
		self.addr = ip + ":" + str(port)
		# self.print_lock = threading.Lock()
		self.MAXBUF = 1024

		self.my_out_peer_info = []
		self.my_in_peer_info = []
		self.my_seed_info = []
		self.my_seeds = []
		self.my_out_peers = []
		self.my_in_peers = []

		# self.lock = threading.Lock()
		self.stop_server = threading.Event()

		self.liveliness_count = {}
		self.ML = {}
		#self.conn_to_ip = {}
		self.make_socket()

	def make_socket(self):
		
		print(self.ip,self.port)
		self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP echo socket
		self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.server_sock.bind((self.ip, self.port))		# Bind to the port
		self.server_sock.settimeout(10.0)
		self.server_sock.listen(5)				 # Now wait for client connection (max 5 clients)

		self.client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP echo socket
		self.client_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		#write to file and register node
		self.register_with_seed()
		self.register_with_peer()
		

	def register_with_seed(self):
		seed_info = get_config(filename)
		seed_size = len(seed_info)
		if (seed_size==0):
			error() #return seed empty
		else:
			reg_size = int(seed_size/2) + 1
			reg_list = random.sample(seed_info, reg_size)
		self.my_seed_info = reg_list

		client_union = []		
		for i in reg_list:
			with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
				ip = i.split(":")[0]
				port = int(i.split(":")[1])
				sock.connect((ip,port))
				reg_msg = "Peer Data:" + str(self.ip) + ":" + str(self.port)

				sock.send_msg(sock, reg_msg.encode('utf-8'))
				sock.close()

			#Now receive data on listner port named server sock
			try:
				conn, addr = self.server_sock.accept()

				try:
					print('rec reg',addr)
					client_list = self.recv_msg(conn)
					client_union = Union(client_union, client_list.split(" "))

		print("Number of peers returned:",len(client_union))
		print(client_union)
		if (len(client_union)==0):
			self.my_out_peer_info = []
		elif (len(client_union) >= 4):
			self.my_out_peer_info = random.sample(client_union, 4)
		else:
			self.my_out_peer_info = random.sample(client_union, len(client_union))
		
	def register_with_peer(self):
		if len(self.my_out_peer_info) ==0:
			return

		for i in self.my_out_peer_info:
			print(i)
			if (i.split(":")[0]==self.ip and i.split(":")[1]==self.port):
				error("can't connect to same ip/port")

			self.connect_peer_node(i)

	def run(self):
		print ("Starting " + self.name)
		
		# Get lock to synchronize threads
		#threadLock.acquire()
		#print_time(self.name, self.counter, 3)
		# Free lock to release next thread
		#threadLock.release()
		while not self.stop_server.is_set():
			try:
				conn, incoming_addr = self.server_sock.accept()
				print("lol")

				try:
					msg = self.recv_msg(self.peer_conn)

					if register_msg(msg):
						addr = msg.split(":")[1]+":"+msg.split(":")[2]
						if addr not in self.my_out_peer_info:
							self.my_out_peer_info.append(addr)

					if liveliness_req(msg):
						#reply
						reply = form_liveliness_reply(msg.split(":")[1], msg.split(":")[2], self.server.ip)
						self.send_msg(self.peer_conn, reply)

					elif liveliness_reply(msg):
						#reply
						self.server.liveliness_count[msg.split(":")[3]] = 0

					elif gossip(msg):
						#reply
						message = msg.split(":")[2]
						md5 = hashlib.md5(message.encode()).hexdigest()
						self.server.lock.acquire()
						if md5 not in self.server.ML.keys():
							self.server.ML[md5] = msg

							#write to file

							exclude = []
							exclude.append(self.peer_address)
							self.server.send_all(message, exclude)
						self.server.lock.release()
					else:
						error("invalid format")
				except socket.timeout:
					pass

				except Exception as e:
					print("Exception in recv")
				# incoming_peer = PeerConnection(self, conn, incoming_addr)
				# incoming_peer.start()
				# self.my_in_peers.append(incoming_peer)
				# self.my_in_peer_info.append(incoming_addr)
				# #self.conn_to_ip[incoming_peer] = incoming_addr
				# if incoming_peer not in self.liveliness_count.keys():
				# 	self.liveliness_count[incoming_peer] = 0
			except socket.timeout:
				pass

			except Exception as e:
				sel.stop_server.set()

	

	def connect_peer_node(self, peer):
		# sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		# sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		# sock.connect((peer.split(":")[0], int(peer.split(":")[1])))

		peer_gossip_thread = PeerConnection(self, peer, 0)
		peer_liveliness_thread = PeerConnection(self, peer, 1)
		peer_gossip_thread.start()
		peer_liveliness_thread.start()

		#self.my_out_peers.append(peer_thread)
		if peer not in self.liveliness_count.keys():
			self.liveliness_count[peer] = 0

	def connect(self, ip, port):
		self.client_sock.connect((ip,port))

	def accept(self):
		conn, addr = self.server_sock.accept()
		#self.print_lock.acquire() 
		self.print('Connected to :', addr[0], ':', addr[1]) 

		# Start a new thread and return its identifier 
		return (conn, addr)
		#start_new_thread(threaded, (c,)) 

	def recv_msg(self, sock, lock=None):
		msg = ""
		while True:
			data = sock.recv(MAXBUF)
			if not data: 
				break
			msg = msg + data.decode('utf-8')
		return msg

	def send_msg(self, sock, msg):
		sock.send(msg)

	def send_all (self, msg, exclude=[]):
		# for i in self.my_in_peers:
		# 	if i.peer_address not in exclude:
		# 		i.send(i.peer_conn, form_gossip_msg(i.split(":")[0], msg))
		for i in self.my_out_peers_info:
			if i not in exclude:
				sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				sock.connect((i.split(":")[0], i.split(":")[1]))
				self.send_msg(sock, msg)




class PeerConnection (threading.Thread):
	def __init__(self, server, address, flag):
		threading.Thread.__init__(self)
		self.server = server
		#self.peer_conn = connection
		self.peer_address = address
		self.stop_server = threading.Event()
		self.gossip_interval = 10
		self.liveliness_interval = 13
		self.message = "Hello"

	def run(self):

		if flag == 0:
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			sock.connect((peer.split(":")[0], int(peer.split(":")[1])))

			msg = form_reg_msg(str(self.server.ip) + ":" + str(self.server.port))
			self.send_msg(sock, msg)

			for i in range(10):
				msg = form_gossip_msg(self.server.addr, self.message)
				self.server.send_all(msg)
				time.sleep(self.gossip_interval)

		elif flag == 1:
			while True:
				msg = form_liveliness_msg(self.server.addr)
				self.server.send_all(msg)
				time.sleep(self.liveliness_interval)
				check_liveliness()				
		else:
			error("wrong flag")

	def check_liveliness (self):
			to_remove = 0
			for i in self.server.liveliness_count:
				if (self.liveliness_count[i] >= 3):
					#close conn

					to_remove = i
					for addr in self.server.my_seed_info:
						sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
						sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
						ip = addr.split(":")[0]
						port = addr.split(":")[1]
						sock.connect((ip,port))
						self.send_msg(sock, form_deadNode_msg(self.peer_address, self.ip))
						sock.close()

			if to_remove != 0:
				del self.liveliness_count[to_remove]
			for i in self.liveliness_count:
				self.liveliness_count[i] = self.liveliness_count[i] + 1


		# while not self.stop_server.is_set():
		# 	try:
		# 		msg = self.recv_msg(self.peer_conn)
		# 		if self.liveliness_req(msg):
		# 			#reply
		# 			reply = form_liveliness_reply(msg.split(":")[1], msg.split(":")[2], self.server.ip)
		# 			self.send_msg(self.peer_conn, reply)

		# 		elif self.liveliness_reply(msg):
		# 			#reply
		# 			self.server.liveliness_count[msg.split(":")[3]] = 0

		# 		elif self.gossip(msg):
		# 			#reply
		# 			message = msg.split(":")[2]
		# 			md5 = hashlib.md5(message.encode()).hexdigest()
		# 			self.server.lock.acquire()
		# 			if md5 not in self.server.ML.keys():
		# 				self.server.ML[md5] = msg

		# 				#write to file

		# 				exclude = []
		# 				exclude.append(self.peer_address)
		# 				self.server.send_all(message, exclude)
		# 			self.server.lock.release()
		# 		else:
		# 			error("invalid format")
		# 	except:
		# 		error("invalid format")
	def send_msg(self, sock, msg):
		try:
			sock.send(msg)
		except:
			error()

def register_msg(msg):
	if msg.split(":")[0] == "Register":
		return True
	else:
		return False

def liveliness_req(msg):
	if (msg.split(":")[0] == "Alive?"):
		return True
	else:
		return False

def liveliness_reply(msg):
	if (msg.split(":")[0] == "Yes, Alive"):
		return True
	else:
		return False

def gossip(msg):
	check=0
	try:
		time = datetime.strptime(msg.split(":")[0], '%Y-%m-%d %H:%M:%S.%f')
		check=1
	except:
		check=0
	return check
def recv_msg(sock):
	msg = ""
	while True:
		data = sock.recv(MAXBUF)
		if not data: 
			print('Bye') 
			#lock.release() #check for lock 
			break
		msg = msg + data
	return msg

			
def get_config(filename):
	with open(filename, "r") as f:
		seed_info=[]
		for line in f:
			seed_info.append(line.strip())
	return seed_info

	# with open(filename, "r") as f:
	# 	check = 0
	# 	seed_info=[]
	# 	for line in f:
	# 		if (check==1):
	# 			seed_info.append(line)
	# 		if (line == "__SEED__"):
	# 			check=1
	# return seed_info

def Union(lst1, lst2):
	lst2 = [i for i in lst2 if i]
	final_list = list(set(lst1) | set(lst2))
	return final_list 

def form_gossip_msg(ip, message):
	msg = ""
	t = datetime.now()
	msg = msg + str(t) + ":" + ip + ":" + message
	return msg

def form_liveliness_req(ip):
	req = "Alive?"
	t = datetime.now()
	req = req + ":" + str(t) + ":" + ip
	return req

def form_liveliness_reply(t, sender_ip, self_ip):
	req = "Yes, Alive"
	req = req + ":" + str(t) + ":" + sender_ip + ":" + self_ip
	return req

def form_deadNode_msg(addr, self_ip):
	msg = "Dead Node"
	t = datetime.now()
	msg = msg + ":" + addr + ":" + str(t) + self_ip
	return msg 

def form_reg_msg(addr):
	msg = "Register"
	msg = msg + addr
	return msg

def error(msg):
	print(msg)