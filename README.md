# Reliable UDP File Transfer Client

This project implements a reliable file transfer protocol over UDP. It is designed to act as a client that downloads a file from a server while managing network congestion and server-side rate limiting.

## Problem Statement

The goal is to reliably download a file (up to 15MB) from a server using UDP. The server introduces two main challenges:
1. Packet Loss: The server randomly drops packets to simulate a lossy network.
2. Rate Limiting (Leaky Bucket): The server uses a leaky bucket algorithm. If the client requests data too quickly, the bucket empties, and the server stops replying. Continued excessive requests result in the client being "squished" (penalized with a lower service rate).

The client must assemble the file from chunks, handle retransmissions, adapt its sending rate to avoid penalties, and verify the final file integrity using an MD5 hash.

## Concepts and Architecture

The solution is built on Python's `socket` library and uses threading to handle sending and receiving operations concurrently.

### 1. Reliable Data Transfer
Since UDP is unreliable, the client implements reliability at the application layer:
- The file is requested in chunks (1448 bytes).
- The client tracks which chunks have been received.
- A loop continues to request missing chunks until the entire file is assembled.

### 2. Congestion Control (AIMD)
To maximize throughput without triggering the server's rate limiter, the client implements an Additive Increase, Multiplicative Decrease (AIMD) algorithm, similar to TCP congestion control.

- Burst Mode: Requests are sent in batches or "bursts".
- Slow Start: Initially, the burst size increases exponentially (doubles) to quickly ramp up speed.
- Congestion Avoidance:
  - If a packet loss is detected (timeout), the burst size is halved (Multiplicative Decrease) and the slow start phase ends.
  - If a burst is successful, the burst size is incremented linearly (Additive Increase).

### 3. Round Trip Time (RTT) Estimation
The client dynamically adjusts its timeouts based on network conditions.
- It measures the time taken for a request to receive a reply.
- It uses an Exponential Weighted Moving Average (EWMA) to smooth the RTT value.
- Formula: New RTT = 0.8 * Sample + 0.2 * Old RTT.
- A high alpha (0.8) is used to react quickly to changes.

## Code Implementation Details

The code is structured into two main classes: `ReliableUDP` and `UDPStream`.

### ReliableUDP Class
Handles the low-level socket operations.
- Wraps Python's `socket` methods.
- Implements a `get` method that sends a message and retries a fixed number of times if no reply is received.
- Implements `flush_buffer` to clear old packets from the socket before starting new operations.

### UDPStream Class
Contains the core logic for the assignment.

**Sending Logic (`send_thread`)**
- Iterates through the list of data chunks.
- Calculates the current `burst_size`.
- Sends requests for missing chunks up to the burst size.
- Sleeps for `1.5 * RTT` to allow time for responses to arrive.
- If packets timeout (implied by the need to resend in the next loop), it triggers the Multiplicative Decrease.
- If the send loop completes a full pass of the file, it resets to scan for remaining gaps.

**Receiving Logic (`recv_thread`)**
- Runs in a continuous loop listening for data.
- Parses the custom header format (Offset, NumBytes, Squished flag).
- Detects the "Squished" flag to log if the server is penalizing the client.
- Updates the `data` array with received payload.
- Updates the RTT estimate using timestamps stored in `burst_dict`.

**Hash Verification**
- Once all chunks are received, the `submit` method calculates the MD5 hash of the assembled data.
- It sends this hash to the server for verification.

## Running Instructions

### Prerequisites
- Python 3.x
- `matplotlib` (Only required if generating the plots at the end)

### Server Setup (Local)
To test locally, use the provided Java server files:

- Constant Rate:
  `java UDPServer 9801 big.txt 10000 constantrate notournament verbose`

- Variable Rate:
  `java UDPServer 9802 big.txt 10000 variablerate notournament verbose`

### Client Execution
1. Open `main.py`.
2. Locate the `execute_bi_stream` function.
3. Uncomment/Edit the `UDPStream` instantiation to match your target IP and Port.
   - For local: `("127.0.0.1", 9801)`
   - For Vayu server: Use the specific IP provided (e.g., `10.17.7.134`).
4. Run the script:
   `python main.py`

### Visualizations
The script will generate two plots upon completion:
- Sending/Receiving History: Visualizes the offset progression over time.
- Burst Size & Squish Events: Shows how the AIMD algorithm adjusted the burst size and indicates when the client was squished.