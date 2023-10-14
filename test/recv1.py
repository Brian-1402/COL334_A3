import socket

UDP_IP = "127.0.0.1"
UDP_PORT = 9802


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Internet  # UDP
host = socket.gethostname()
print(socket.gethostbyname_ex(host))
sock.bind((UDP_IP, UDP_PORT))
sock.settimeout(5)
input("start waiting to receive?: ")
try:
    while True:
        data, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
        print(data.decode())
except:
    pass

sock.close()
