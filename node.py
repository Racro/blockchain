import random
import threading
from datetime import datetime

filename = "config.txt"

class Seed_Node (threading.Thread):
	def __init__(self, ip, port, name):
		threading.Thread.__init__(self)
		self.ip = ip
		self.name = name
		self.port = port
		self.client_list = []
		self.client_conn = []
		self.stop_server = threading.Event()
		self.init_seed_server()

	def init_seed_server(self):
		self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP echo socket
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.server_sock.bind((self.ip, self.port))        # Bind to the port
		self.server_sock.listen(5)                 # Now wait for client connection (max 5 clients)
	
	def run(self):
		def run(self):
		print ("Starting " + self.name)
		# Get lock to synchronize threads
		#threadLock.acquire()
		#print_time(self.name, self.counter, 3)
		# Free lock to release next thread
      	#threadLock.release()
   
	   	while not stop_server.is_set():
	   		try:
	      		conn, incoming_addr = self.server_sock.accept()
	      		if incoming_addr not in self.client_list:
	      			self.client_list.append(incoming_addr)
	      			self.client_conn.append(conn)

	      		#msg = clientlist
	      		msg = ""
	      		for i in self.client_list:
	      			msg = msg + i + " "
	      		self.send(conn, msg)
	      	except Exception as e:
				self.stop_server.set()

	def send(sock, msg):
		sock.send(msg)


class Peer_Node (threading.Thread):
	def __init__(self, ip, port, name):
		threading.Thread.__init__(self)
		self.ip = ip
		self.name = name
		self.port = port
		self.print_lock = threading.Lock()
		self.MAXBUF = 1024

		self.my_out_peer_info = []
		self.my_in_peer_info = []
		self.my_seed_info = []
		self.my_out_peers = []
		self.my_in_peers = []

		self.lock = threading.Lock()
		self.stop_server = threading.Event()

		self.ML = {}
		#self.conn_to_ip = {}
		self.make_socket()

	def make_socket(self):
		self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP echo socket
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.server_sock.bind((self.ip, self.port))        # Bind to the port
		self.server_sock.listen(5)                 # Now wait for client connection (max 5 clients)

		self.client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP echo socket
        self.client_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		#write to file and register node

		self.register_with_seed()

	def run(self):
		print ("Starting " + self.name)
		# Get lock to synchronize threads
		#threadLock.acquire()
		#print_time(self.name, self.counter, 3)
		# Free lock to release next thread
      	#threadLock.release()
      	try:
	      	while not stop_server.is_set():
	      		conn, incoming_addr = self.server_sock.accept()

	      		incoming_peer = PeerConnection(self, conn, incoming_addr)
	      		incoming_peer.start()
	      		self.my_in_peers.append(incoming_peer)
	      		self.my_in_peer_info.append(incoming_addr)
	      		#self.conn_to_ip[incoming_peer] = incoming_addr
      		

    def register_with_peer(self, peer_list):
    	for i in peer_list:
    		if (i.split(":")[0]==self.ip || i.split(":")[1]==self.port):
    			error("can't connect to same ip/port")
    		if i in self.my_out_peer_info:
    			error("already connected")
    		self.connect_peer_node(i)
    		self.my_out_peer_info.append(i)

    def connect_peer_node(self, peer):
    	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    	sock.connect((peer.split(":")[0], peer.split(":")[1]))

    	peer_thread = PeerConnection(self, sock, peer)
    	peer_thread.start()
    	self.my_out_peers.append(peer_thread)

    def register_with seed(self):
    	#get seed info - ["ip:port", ]
    	seed_info = getcofig(filename)
    	seed_size = len(seed_info)
    	if (seed_size==0):
    		error #return seed empty
    	else:
    		reg_size = int(seed_size/2) + 1
    		reg_list = random.sample(seed_info, reg_size)
    	self.my_seed_info = reg_list

		client_union = []    	
    	for i in reg_list:
    		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    		ip = i.split(":")[0]
    		port = i.split(":")[1]
			sock.connect((ip,port))

			client_list = ""
    		while True:
    			data = sock.recv(self.MAXBUF)
    			if not data: 
            		print('Bye') 
	            	#lock.release() #check for lock 
    	        	break
    	        client_list = client_list + data #received as string - "ip1:port1 ip2:port2 ..."

    	    client_union = Union(client_union, client_list.split(" "))

    	    sock.close()

    	if (len(client_union)==0):
    		error #return client_union empty
    	elif (len(client_union) >= 4):
    		my_out_peer_info = random.sample(client_union, 4)
    	else:
    		my_out_peer_info = random.sample(client_union, len(client_union))
    	self.register_with_peer(my_out_peer_info)

    def connect(self, ip, port):
    	self.client_sock.connect((ip,port))

    def accept(self):
    	conn, addr = self.server_sock.accept()
    	#self.print_lock.acquire() 
        self.print('Connected to :', addr[0], ':', addr[1]) 
  
        # Start a new thread and return its identifier 
        return (conn, addr)
        #start_new_thread(threaded, (c,)) 

    def recv_msg(self, sock, lock):
    	msg = ""
    	while True:
    		data = sock.recv(MAXBUF)
    		if not data: 
            	print('Bye') 
	            #lock.release() #check for lock 
    	        break
    	    msg = msg + data
    	return msg

   	def send_msg(self, sock, msg):
    	sock.send(msg)

    def send_all (self, msg, exclude=[]):
    	for i in self.my_in_peers:
    		if i.peer_address not in exclude:
    			i.send(i.peer_conn, form_gossip_msg(i.split(":")[0], msg))
    	for i in self.my_out_peers:
    		if i.peer_address not in exclude:
    			i.send(i.peer_conn, form_gossip_msg(i.split(":")[0], msg))

class PeerConnection (threading.Thread):
	def __init__(self, server, connection, address):
		threading.Thread.__init__(self)
		self.server = server
		self.peer_conn = connection
		self.peer_address = address
		self.stop_server = threading.Event()

	def run(self):
      	while not stop_server.is_set():
      		try:
	      		msg = self.recv_msg(self.peer_conn)
	      		if self.liveliness_req(msg):
	      			#reply
	      		elif self.liveliness_reply(msg):
	      			#reply
	      		elif self.gossip(msg):
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
	      			#error(invalid format)
	      		#write to file

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
	def recv_msg(self, sock):
    	msg = ""
    	while True:
    		data = sock.recv(MAXBUF)
    		if not data: 
            	print('Bye') 
	            #lock.release() #check for lock 
    	        break
    	    msg = msg + data
    	return msg

	def send_msg(self, msg):
		try:
			self.peer_conn.send(msg)
			
def get_config(filename):
	with open(filename, "r") as f:
		check = 0
		seed_info=[]
		for line in f:
			if (check==1):
				seed_info.append(line)
			if (line == "__SEED__"):
				check=1
	return seed_info

def Union(lst1, lst2):
	final_list = list(set(lst1) | set(lst2))
	return final_list 

def form_gossip_msg(ip, message):
	msg = ""
	t = datetime.now()
	msg = msg + str(t) + ":" + ip + ":" + message
	return msg