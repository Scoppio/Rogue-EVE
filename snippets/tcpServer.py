import socket
import json

def Main():
  print(
  """
  EVE-ROGUE

  developed in python 3.5
  by Lucas Scoppio
  """)

  host = '127.0.0.1'
  port = 5000

  s = socket.socket()
  s.bind((host,port))

  s.listen(1000)
  c, addr = s.accept()
  print("Connection from",addr)
  try:
    while True:
      data = c.recv(4096) #1024 bytes
      if not data:
        break
      
      if "handshake" in str(data):
        print("from connected user:", str(data))

        data = "CONNECTED TO SERVER"
        print("sending:", data)
        c.send(data.encode())
      else:
        print(data.decode())
        c.send(data)

  finally:
    c.close()

if __name__ == "__main__":
  Main()