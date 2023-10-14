import socket

UDP_IP = "127.0.0.1"
UDP_PORT = 9801
MESSAGE = b"SendSize\n\n"

print("UDP target IP: %s" % UDP_IP)
print("UDP target port: %s" % UDP_PORT)
print("message: %s" % MESSAGE)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Internet  # UDP
sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
while True:
    data, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
    print(data.decode())
