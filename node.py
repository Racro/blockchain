import random
import threading
from datetime import datetime
import socket
import time
import hashlib

filename = "config.csv"
MAXBUF = 1024

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
		self.server_sock.listen(5)				 # Now wait for client connection (max 5 clients)

	def run(self):
		print ("Starting " + self.name)
		while not self.stop_server.is_set():
			try:
				conn, incoming_addr = self.server_sock.accept()
				print(self.name + " received con from: ", incoming_addr)

				try:
					msg = self.recv_msg(conn)

					# print(msg)
					if msg.split(":")[0] == "Register":
						incoming_addr = (str(msg.split(":")[1]),int(msg.split(":")[2])) #strored as tuple
						write_to_terminal(msg)
						write_to_file(self.file, msg)
						
						print(incoming_addr)
						msg = ""
						for i in self.client_list:
							msg = msg + i[0] + ":" + str(i[1]) + " "
						msg = form_clientList_msg(msg, self.addr)
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
				print(repr(e))
				print("Foo")
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
	def __init__(self, ip, port, message, name):
		threading.Thread.__init__(self)
		self.ip = ip
		self.name = name
		self.port = int(port)
		self.addr = ip + ":" + str(port)
		# self.print_lock = threading.Lock()
		#self.MAXBUF = 1024
		self.message = message
		self.peer_info = []
		self.seed_info = []
		
		self.file = name + ".txt"
		self.lock = threading.Lock()
		self.stop_server = threading.Event()
		self.liveliness_count = {}
		self.ML = {}

		self.peer_threads = []
		#self.conn_to_ip = {}
		self.make_socket()

	def make_socket(self):
		
		print(self.ip,self.port)
		self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP echo socket
		self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.server_sock.bind((self.ip, self.port))		# Bind to the port
		# self.server_sock.settimeout(10.0)
		self.server_sock.listen(5)				 # Now wait for client connection (max 5 clients)

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
		print("Seed info for:", self.name, repr(self.seed_info))

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
				
		print("Number of peers returned:",len(client_union))	
		print(client_union)
		self.peer_info = random.sample(client_union, min(4,len(client_union)))
		

	def register_with_peer(self):
		for i in self.peer_info:
			ip,port = i.split(":")[0],int(i.split(":")[1])
			if (ip==self.ip and port==self.port):
				error("can't connect to same ip/port")

			#Now send self adress to the old established peer
			addr = (ip,port)
			reg_msg = form_reg_msg(str(self.ip) + ":" + str(self.port))
			self.send_msg(reg_msg,addr)

			if i not in self.liveliness_count.keys():
				self.liveliness_count[i] = 0

	def spawn_communication_threads(self):
		#start gossip
		peer_gossip_thread = PeerConnection(self,0)
		peer_gossip_thread.start()
		self.peer_threads.append(peer_gossip_thread)		
		
		# start liveliness
		peer_liveliness_thread = PeerConnection(self,1)
		peer_liveliness_thread.start()
		self.peer_threads.append(peer_liveliness_thread)		


		# if peer not in self.liveliness_count.keys():
		# 	self.liveliness_count[peer] = 0

	def run(self):
		print ("Starting " + self.name)
		
		while not self.stop_server.is_set():
			try:
				conn, incoming_addr = self.server_sock.accept()
				try:
					msg = self.recv_msg(conn)

					print("MESSAGE RECIEVED:",msg)

					if self.register_msg(msg):
						addr = msg.split(":")[1]+":"+msg.split(":")[2]
						if addr not in self.peer_info:
							self.peer_info.append(addr)

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
						message = msg.split(":")[:4]
						incoming_addr = msg.split(":")[-2:]
						md5 = hashlib.md5(message.encode()).hexdigest()
						# self.server.lock.acquire()
						if md5 not in self.ML.keys():
							self.ML[md5] = True
							print_msg = str(datetime.now()) + ":" + incoming_addr + ":" + message[-1] 
							write_to_terminal(print_msg)
							write_to_file(self.file, print_msg)
							#write to file
							#check for exclusion of address from where recieved gossip msg
							
							exclude = []
							exclude.append(incoming_addr)
							msg = form_gossip_msg(self.addr, message, 1)
							self.broadcast(msg, exclude)

						# self.server.lock.release()
					else:
						print("*"*20)
						print(msg)
						error("invalid format")
						print("*"*20)
				except socket.timeout:
					error("timeout in peer recv")
					pass

				except Exception as e:
					print(e)
			except socket.timeout:
				error("timeout in peer accept")
				pass

			except Exception as e:
				write_to_terminal(e)
				for i in peer_threads:
					i.join()
				self.stop_server.set()
		self.server_sock.close()
	

	def send_msg(self, msg,addr):
		try:
			self.lock.acquire()
			with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
				s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				s.connect(addr)
				s.sendall(msg.encode('utf-8'))
			s.close()
			self.lock.release()
		except:
			self.lock.release()
			error("couldn't send msg" + msg)

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
		print(msg)
		time = datetime.strptime(msg.split(":")[0], '%d-%m-%Y-%H-%M-%S')
		check=1
	
		return check


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
				msg = form_gossip_msg(self.addr, self.server.message, 0)
				
				# try:
					# self.server.lock.acquire()
				self.server.broadcast(msg)
					# self.server.lock.release()

				# except:
					# self.server.lock.acquire()
					# self.server.lock.release()
				# error("coudn't send gossip")
					# self.server.lock.release()
					
				time.sleep(self.gossip_interval)

		elif self.flag == 1:
			while True:
				msg = form_liveliness_req(self.server.addr)
				print(msg)
				# try:
					# self.server.lock.acquire()
				self.server.broadcast(msg)
					# self.server.lock.release()
				# except:
					# self.server.lock.release()
				# error("coudn't send liveliness")

				time.sleep(self.liveliness_interval)
				self.check_liveliness()				
		else:
			error("wrong flag")

	def check_liveliness (self):
			print(self.server.peer_info)
			to_remove = []
			for i in self.server.liveliness_count:
				if (self.server.liveliness_count[i] >= 3):

					to_remove.append(i)
					print(to_remove)
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
			self.server.lock.acquire()
			with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
				s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				s.connect(addr)
				s.sendall(msg.encode('utf-8'))
			self.server.lock.release()
		except:
			self.server.lock.release()
			error("couldn't semd msg" + msg)

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


def form_reg_msg( addr):
	msg = "Register:"
	msg = msg + addr
	return msg


def send_msg( sock, msg):
	try:
		sock.send(msg)
	except:
		error("can't send msg")

def write_to_file(file, msg):
	f = open(file, "a+")
	f.write(msg)
	f.write("\n")
	f.close()

def write_to_terminal(msg):
	print(msg)