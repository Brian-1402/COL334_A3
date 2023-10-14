import socket

UDP_IP = "127.0.0.1"
UDP_PORT = 9803
UDP_IP_RECEIVER = "127.0.0.1"
UDP_PORT_RECEIVER = 9803


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Internet  # UDP

sock.bind((UDP_IP, UDP_PORT))

sock.settimeout(2)
host = socket.gethostname()
print(socket.gethostbyname_ex(host))


def send(s, message):
    s.sendto(message, (UDP_IP_RECEIVER, UDP_PORT_RECEIVER))


def send_retry(s, message, tries=5):
    s.sendto(message.encode(), (UDP_IP_RECEIVER, UDP_PORT_RECEIVER))
    count = 0
    while count < tries:
        try:
            data, addr = sock.recvfrom(2048)
            break
        except socket.timeout:
            print("Timed out, retrying")
            count += 1
    else:
        print("Failed to receive, stopping attempt")
    return data.decode()


def send_burst(s):
    for i in range(5):
        s.sendto(f"message {i+1}".encode(), (UDP_IP_RECEIVER, UDP_PORT_RECEIVER))


def catch_burst(s):
    count = 0
    while count < 5:
        try:
            data, addr = sock.recvfrom(2048)
            print(data.decode())
            count += 1
        except socket.timeout:
            print("Timed out, retrying")
            count += 1
    # else:
    #     print("Failed to receive, stopping attempt")
    # return data.decode()


import time

try:
    # print(send_retry(sock, "SendSize\n\n"))
    send_burst(sock)
    time.sleep(10)
    catch_burst(sock)
except Exception as e:
    print(e, "\n\nError, closing")


sock.close()
