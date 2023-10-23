import socket, time, datetime, hashlib, math
from matplotlib import pyplot as plt


class ReliableUDP:
    def __init__(
        self,
        send_addr,
        recv_addr=None,
        timeout=2,
    ):
        self.send_addr = send_addr
        if not recv_addr:
            self.recv_addr = (socket.gethostbyname_ex(socket.gethostname())[2][-1], 0)
            # self.recv_addr = ("0.0.0.0", 0)
        else:
            self.recv_addr = recv_addr
        self.timeout = timeout
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.bind(self.recv_addr)
        self.s.settimeout(timeout)

    def __del__(self):
        self.s.close()

    def send(self, message):
        self.s.sendto(message.encode(), self.send_addr)

    def recv(self):
        reply, addr = self.s.recvfrom(2048)
        if addr != self.send_addr:
            raise RuntimeError("Wrong server IP")
        return reply.decode()

    def get(self, message, tries=5):
        self.flush_buffer()
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
            raise ConnectionError("Failed to connect")
        return reply

    def flush_buffer(self):
        """Should be called after ample time is given,
        for expected leftover requests to pile up and be flushed"""
        self.s.setblocking(False)
        flushed = 0
        while True:
            try:
                d = self.s.recvfrom(2048)
                flushed += 1
                print("Flushed once")
            except BlockingIOError:
                break
        if flushed:
            print(f"Flushed {flushed} packets\n")
        self.s.settimeout(self.timeout)


class UDPStream:
    def __init__(
        self,
        send_addr,
        entryID,
        team,
        recv_addr=None,
        timeout=2,
    ):
        self.udp = ReliableUDP(send_addr, recv_addr, timeout)
        self.s = self.udp.s

        self.psize = 1448
        self.data = []
        self.size = 0
        self.last_size = 0

        self.entryID = entryID
        self.team = team
        self.hash = ""

    def __del__(self):
        del self.udp

    def getsize(self):
        response = self.udp.get("SendSize\nReset\n\n")
        if response:
            self.size = int(response.split()[1])
            self.data = [None] * math.ceil(self.size / self.psize)
            print(f"Response: \n{response}")

    def parse(self,message):
        '''parses message to produce a dictionary with offset, numbytes (and data). 
        Note - message is pre-decoded'''
        parse_dict = {}
        message_list = message.split("\n")
        parse_dict["Offset"] = int((message_list[0].split())[1])
        parse_dict["NumBytes"] = int((message_list[1].split())[1])
        is_squished = False
        data_start_offset = 0 #Tells where the data starts in message_list -> for the case of squished and non-squished
        if len(message_list)>3:
            if message_list[2]=="Squished" and message_list[3]=="":
                is_squished = True
                data_start_offset+=1
            parse_dict["Squished"] = is_squished
            parse_dict["Data"] = "\n".join(message_list[3+data_start_offset:])
        return parse_dict

    def produce_hash(self):
        """generates and returns hash of data.
        Uses hashlib.md5 and result.hexdigest()"""
        output_data = "".join(self.data)
        result = hashlib.md5(output_data.encode())
        self.hash = result.hexdigest()

    def submit(self):
        message = f"Submit: {self.entryID}@{self.team}\nMD5: {self.hash}\n\n"
        output = (self.udp.get(message)).split()
        if output[1] == "true":
            print(
                f"Submission Success\nTotal time taken: {output[3]}\nPenalty occured: {output[5]}"
            )
        else:
            print("Submission Failed")


def test_flush():
    stream = UDPStream(("127.0.0.1", 9801), None, None, ("127.0.0.1", 9803))
    stream.getsize()
    time.sleep(1)
    stream.udp.send("Offset: 0\nNumBytes: 1448\n\n")
    stream.udp.send("Offset: 1448\nNumBytes: 1448\n\n")
    time.sleep(0.1)
    stream.udp.flush_buffer()
    stream.udp.send("Offset: 1448\nNumBytes: 1448\n\n")
    print(stream.udp.recv())

def test_parse():
    stream = UDPStream(("127.0.0.1", 9801), None, None, ("127.0.0.1", 9803))
    stream.getsize()
    time.sleep(1)
    stream.udp.send("Offset: 1448\nNumBytes: 1448\n\n")
    message = stream.udp.recv() #For Testing general messages (wont be squished cos only one message)
    # message = "Offset: 0\nNumbytes: 1448\nSquished\n\nblahblahblah\nblahblah\nhello" #For Testing squished
    print(stream.parse(message))
    print(stream.parse(message)["Data"])
    print(len(stream.parse(message)["Data"]))

def main():
    test_parse()
    pass


if __name__ == "__main__":
    main()
