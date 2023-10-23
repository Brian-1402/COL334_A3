import socket, time, datetime, hashlib, math, threading
from matplotlib import pyplot as plt

now = datetime.datetime.now


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
        return reply.decode()

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
        timeout=5,
    ):
        self.udp = ReliableUDP(send_addr, recv_addr, timeout)
        # self.udp_s = ReliableUDP(send_addr, ("0.0.0.0", 0), timeout)
        self.s = self.udp.s

        self.psize = 1448
        self.data = []
        self.size = 0
        self.last_size = 0

        self.entryID = entryID
        self.team = team
        self.hash = ""

        self.send_hist = []
        self.recv_hist = []
        self.send_time_hist = []
        self.recv_time_hist = []
        self.start_time = 0

        self.RTT = 0.02
        self.burst_size = 5

    def __del__(self):
        del self.udp

    def getsize(self):
        response = self.udp.get("SendSize\nReset\n\n")
        if response:
            self.size = int(response.split()[1])
            self.data = [None] * math.ceil(self.size / self.psize)
            print(f"Response: \n{response}")

    def parse(self, message):
        """parses message to produce a dictionary with offset, numbytes (and data).
        Note - message is pre-decoded"""
        parse_dict = {}
        message_list = message.split("\n")
        parse_dict["Offset"] = int((message_list[0].split())[1])
        parse_dict["NumBytes"] = int((message_list[1].split())[1])
        is_squished = False
        data_start_offset = 0  # Tells where the data starts in message_list -> for the case of squished and non-squished
        if len(message_list) > 3:
            if message_list[2] == "Squished" and message_list[3] == "":
                is_squished = True
                data_start_offset += 1
            parse_dict["Squished"] = is_squished
            parse_dict["Data"] = "\n".join(message_list[3 + data_start_offset :])
        return parse_dict

    def produce_hash(self):
        """generates and returns hash of data.
        Uses hashlib.md5 and result.hexdigest()"""
        output_data = "".join(self.data)
        result = hashlib.md5(output_data.encode())
        self.hash = result.hexdigest()

    def submit(self):
        self.produce_hash()
        time.sleep(0.1)
        message = f"Submit: {self.entryID}@{self.team}\nMD5: {self.hash}\n\n"
        output = self.udp.get(message)
        # print("Submitted, output:\n\n", output)
        output = output.split()
        if output[1] == "true":
            print(
                f"\n\nSubmission Success\nTotal time taken: {output[3]}\nPenalty occured: {output[5]}"
            )
        else:
            print("Submission Failed")

    def send_thread(self):
        self.stop = False
        i0 = 0
        passes = 0
        while not self.stop:
            burst_count = 0

            while burst_count < self.burst_size:  # math.floor(self.burst_size)
                i = i0 % (len(self.data))

                if not self.data[i]:
                    numbytes = self.psize
                    if i == len(self.data) - 1:
                        numbytes = self.size % self.psize
                    message = f"Offset: {self.psize*i}\nNumBytes: {numbytes}\n\n"

                    print(f"Sending {i}")
                    self.send_time_hist.append(time.time() - self.start_time)
                    self.send_hist.append(self.psize * i)
                    self.udp.send(message)
                    burst_count += 1

                if i == len(self.data) - 1:
                    passes += 1
                    break
                i0 += 1
                # After each pass, give it RTT time to receive any pending requests
                # Becomes more relevant in later passes when only few packets are remaining to receive
                # print("i")

            time.sleep(self.RTT)
            # if above time delay is long enough for all packets to receive,
            # then below code will ensure no duplicate sent packets.
            if i0 % len(self.data) == len(self.data) - 1:
                if None not in self.data:
                    self.stop = True
                    break
                elif self.stop == True:
                    raise RuntimeError
                #! CHECK FOR MORE LOGICAL ISSUES TO ADD AS ELIFs
                else:
                    i0 += 1
        print("Sending thread stopped")

    def recv_thread(self):
        self.s.settimeout(2 * self.RTT)
        # self.s.setblocking(False)
        self.stop = False
        count = 0
        retry = 0
        while not self.stop:
            if count > len(self.data):
                if None not in self.data:
                    self.stop = True
                    break
            try:
                response = self.udp.recv()
            except socket.timeout:
                print("Timed out")
                if None not in self.data:
                    self.stop = True
                    break
                else:
                    if retry < 20:
                        retry += 1
                        continue
                    else:
                        raise ConnectionError
            retry = 0
            d = self.parse(response)
            print(f"Received {d['Offset']//self.psize}")
            if d["NumBytes"] != len(d["Data"]):
                continue
            # burst_size+= 1/
            self.recv_time_hist.append(time.time() - self.start_time)
            self.recv_hist.append(d["Offset"])
            self.data[d["Offset"] // self.psize] = d["Data"]
            count += 1
        print("Receive thread ended")

    def bi_stream(self):
        st = threading.Thread(target=self.send_thread, daemon=True)
        rt = threading.Thread(target=self.recv_thread, daemon=True)
        self.udp.flush_buffer()
        self.start_time = time.time()
        st.start()
        rt.start()
        st.join()
        # time.sleep(1)
        rt.join()


def execute_bi_stream():
    stream = UDPStream(("127.0.0.1", 9801), "2021CS50609", "Team", ("127.0.0.1", 9803))
    stream.getsize()
    stream.bi_stream()
    stream.submit()
    plt.scatter(
        stream.send_time_hist,
        stream.send_hist,
        label="Sending history",
        color="b",
        zorder=1,
    )
    plt.scatter(
        stream.recv_time_hist,
        stream.recv_hist,
        label="Receiving history",
        color="orange",
        zorder=0,
    )
    plt.legend(loc="best")
    plt.xlabel("time")
    plt.ylabel("offset")
    # plt.show()


def main():
    # try:
    execute_bi_stream()
    # except Exception as e:
    #     print(e)


if __name__ == "__main__":
    main()
