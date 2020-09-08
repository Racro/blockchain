import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("127.0.0.2", 8080))
s.connect(("127.0.0.1", 12345))
s.send(b'try1')
s.close()