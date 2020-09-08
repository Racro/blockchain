# import socket programming library 
import socket 
import time

# import thread module 
from _thread import *
import threading 

print_lock = threading.Lock() 

# thread function 
def threaded(c): 
	while True: 

		# data received from client 
		data = c.recv(1024) 
		if not data: 
			print('Bye') 
			
			# lock released on exit 
			print_lock.release() 
			break

		# reverse the given string from client 
		data = data[::-1] 

		# send back reversed string to client 
		c.send(data) 

	# connection closed 
	c.close() 


def Main(): 
	host = "127.0.0.1" 
	# reverse a port on your computer 
	# in our case it is 12345 but it 
	# can be anything 
	port = 12345
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
	s.bind((host, port))
	s.settimeout(5) 
	print("socket binded to port", port) 

	# put the socket into listening mode 
	s.listen(1) 
	print("socket is listening") 
	# a forever loop until client wants to exit 
	while True: 

		# establish connection with client
		print("starting accept")
		try: 
			c, addr = s.accept()
		except socket.timeout:
			print("HOLA")
		print(addr) 
		buf = c.recv(100)
		print(repr(buf))
		time.sleep(20)

		# lock acquired by client 
		#print_lock.acquire() 
		#print('Connected to :', addr[0], ':', addr[1]) 

		# Start a new thread and return its identifier 
		#start_new_thread(threaded, (c,)) 
	s.close() 


if __name__ == '__main__': 
	Main() 
