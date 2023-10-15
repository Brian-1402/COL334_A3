import socket, time, datetime, hashlib


class ReliableUDP:
    def __init__(
        self,
        send_addr,
        entryID,
        team,
        recv_addr=None,
        timeout=2,
    ):
        self.send_addr = send_addr
        if not recv_addr:
            self.recv_addr = (socket.gethostbyname_ex(socket.gethostname())[2][-1], 0)
        else:
            self.recv_addr = recv_addr
        self.timeout = timeout
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print(recv_addr)
        print(send_addr)
        self.s.bind(self.recv_addr)
        self.s.settimeout(timeout)

        self.psize = 1448
        self.data = []
        self.size = 0
        self.last_size = 0

        self.entryID = entryID
        self.team = team
        self.hash = ""

    def __del__(self):
        self.s.close()

    def send(self, message):
        # self.s.sendto(message.encode(),("127.0.0.1",9801))
        self.s.sendto(message.encode(), self.send_addr)

    def recv(self):
        # try:
        reply, addr = self.s.recvfrom(2048)
        if addr != self.send_addr:
            raise RuntimeError("Wrong server IP")
        return reply.decode()
        # except socket.timeout:
        #     raise TimeoutError("Timed out")

    def get_retry(self, message, tries=5):
        self.send(message)
        count = 0
        reply = ""
        while count < tries:
            try:
                reply, addr = self.s.recvfrom(2048)
                if addr != self.send_addr:
                    continue
                break
            except socket.timeout:
                print("Timed out, retrying")
                count += 1
        else:
            # print("Failed to connect.")
            raise ConnectionError("Failed to connect")
            return
        return reply

    def flush_recv(self):
        self.s.setblocking(False)
        while True:
            try:
                self.s.recvfrom(2048)
            except:
                break
        self.s.settimeout(self.timeout)

    def getsize(self):
        response = self.get_retry("SendSize\nReset\n\n")
        if response:
            self.size = int(response.split()[1])
            self.data = [None] * (self.size // self.psize + 1)
            print(f"Response: \n{response}")
            # CHECK here

    def produce_hash(self):
        """generates and returns hash of data.
        Uses hashlib.md5 and result.hexdigest()"""
        output_data = "".join(self.data)
        result = hashlib.md5(output_data.encode())
        self.hash = result.hexdigest()

    def submit(self):
        message = f"Submit: {self.entryID}@{self.team}\nMD5: {self.hash}\n\n"
        output = (self.get_retry(message)).split()
        if output[1] == "true":
            print(
                f"Submission Success\nTotal time taken: {output[3]}\nPenalty occured: {output[5]}"
            )
        else:
            print("Submission Failed")


# test_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# test_sock.bind(("127.0.0.1",9804))
# test_sock.sendto("SendSize\nReset\n\n".encode(),("127.0.0.1",9801))
# result = test_sock.recvfrom(2048)
# print(result)
udp = ReliableUDP(("127.0.0.1", 9801), None, None, ("127.0.0.1", 9803))
udp.getsize()
time.sleep(5)
udp.send("Offset: 0\nNumBytes: 1448\n\n")
udp.send("Offset: 1448\nNumBytes: 1448\n\n")
print(udp.recv())
print(udp.recv())
