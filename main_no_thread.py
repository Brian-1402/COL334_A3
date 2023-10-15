import socket,math,time,hashlib
from matplotlib import pyplot as plt

def parse(message):
        '''parses message to produce a dictionary with offset, numbytes (and data). 
        Note - message is pre-decoded'''
        parse_dict = {}
        message_list = message.split("\n")
        parse_dict["Offset"] = int((message_list[0].split())[1])
        parse_dict["NumBytes"] = int((message_list[1].split())[1])
        if len(message_list)>3:
            parse_dict["Data"] = "\n".join(message_list[3:])
        return parse_dict

UDP_IP = "127.0.0.1"
UDP_PORT = 9803
UDP_IP_RECEIVER = "127.0.0.1"
UDP_PORT_RECEIVER = 9801

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Internet  # UDP

s.bind((UDP_IP, UDP_PORT))

timeout = 2
s.settimeout(timeout)
host = socket.gethostname()
print(socket.gethostbyname_ex(host))

s.sendto("SendSize\nReset\n\n".encode(), (UDP_IP_RECEIVER, UDP_PORT_RECEIVER))
reply, addr = s.recvfrom(2048)
data_size = int(reply.split()[1])

total_data_count = math.ceil(data_size/1448)
data = [None]*(total_data_count)
data_count = 0
print(total_data_count)
ind = 0

s.setblocking(False)
while ind < len(data) and data_count < total_data_count:
    dat = data[ind]
    if dat == None:
        time.sleep(0.01)
        if ind != total_data_count -1:
            s.sendto(f"Offset: {1448*ind}\nNumBytes: 1448\n\n".encode(),(UDP_IP_RECEIVER, UDP_PORT_RECEIVER))
        else:
            s.sendto(f"Offset: {1448*ind}\nNumBytes: {data_size%1448}\n\n".encode(),(UDP_IP_RECEIVER, UDP_PORT_RECEIVER))

    if ind == total_data_count-1:
        ind = 0
    else:
        ind+=1
    try:
        message,addr = s.recvfrom(2048)
        parsed_dict = parse(message.decode())
        data[parsed_dict["Offset"]//1448] = parsed_dict["Data"]
        data_count+=1
        print(data_count,parsed_dict["Offset"]//1448)
        # print(message.decode())
        # print(parsed_dict["Data"])
    except:
        continue

print("Exited")
res = [i for i, val in enumerate(data) if val == None]
print(res)

flushed = 0
while True:
    try:
        d = s.recvfrom(2048)
        flushed += 1
        print("Flushed once")
    except BlockingIOError:
        break
if flushed:
    print(f"Flushed {flushed} packets\n")
s.settimeout(timeout)

output_data = "".join(data)
result = hashlib.md5(output_data.encode())
hashval = result.hexdigest()
print(hashval)
message = f"Submit: 2021CS50607@hello\nMD5: {hashval}\n\n"
print(message)
s.sendto(message.encode(),(UDP_IP_RECEIVER, UDP_PORT_RECEIVER))
time.sleep(1)
output = s.recvfrom(2048)
print(output)
output = (output[0].decode()).split()
if output[1] == "true":
    print(
        f"Submission Success\nTotal time taken: {output[3]}\nPenalty occured: {output[5]}"
    )
else:
    print("Submission Failed")

file1 = open("output.txt", "w") 
file1.write(output_data)
file1.close()




