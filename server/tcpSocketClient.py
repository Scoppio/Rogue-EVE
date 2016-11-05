# Python TCP Client A
import socket 
import time

host = socket.gethostname() # "127.0.0.1"
port = 2004
BUFFER_SIZE = 1024
MESSAGE = input("tcpClientA: Enter message/ Enter exit:") 
 
tcpClientA = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
tcpClientA.connect((host, port))
 
while MESSAGE != 'exit':
    tcpClientA.send(MESSAGE.encode())     
    data = tcpClientA.recv(BUFFER_SIZE)
    print (" Client received data:", data)
    MESSAGE = "a - " + str(time.ctime())
    time.sleep(1)
 
tcpClientA.close() 