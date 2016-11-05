import socket
import json

def Main():
  host = '127.0.0.1'
  port = 5000

  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  s.bind((host,port))

  print("Server Started")

  # we do not list, we only receive data and send data

  while True:
    data, addr = s.recvfrom(4096) #1024 bytes
    
    if "handshake" in str(data):
      print("from connected user:", str(data))

      data = "CONNECTED TO SERVER"
      print("sending:", data)
      s.sendto(data.encode(), addr) # sending back to the address we receive
    else:
      print(">>>",addr,"->",data.decode())

  s.close()

if __name__ == "__main__":
  Main()