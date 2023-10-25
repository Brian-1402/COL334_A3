## Todo:

- Make recv robust to move on when timeout occurs instead of exception and stopping.

- Make the sending and receiving threads.

- check if UDP also has the same issue of data coming halfway and requiring recv in a loop to get complete data, like in TCP in A2.

  - Ans: apparently it doesn't? sort of read somewhere that for TCP specifically it is a stream based protocol and not packet based, so packets would be split up etc etc. So it could imply the opposite for UDP, need to confirm.

- deque implementation for sending pending requests.

## Possible code structure ideas:

### Modular approach

- Separate classes for UDP features and Application specific tasks.

#### Extra functions for ReliableUDP:

- message_id(), response_id().

  - These are used by the ReliableUDP class to match messages with responses. They both should return the same data value which can be equated.
  - _These will be needed for the assignment anyways._

- get_burst()

  - Will take input a list of messages, send rate, and the above functions. Tries to send all together in one go, and after that, do recvfrom in non blocking manner until recvfrom returns blank. Then checks for dropped responses and flush and retry just for those.
  - May not be used that much.

- get_stream()
  - This may be too application specific and shouldn't be in ReliableUDP.
  - Can have many different implementations, like:
    1. running get_burst() for pieces of the data, which will always try to complete a full piece before moving to the next section. Needs just one thread.
    2. (recommended) Have two threads, one for sending and other for receiving. Sending thread does a full pass through the data, and retries for missed out pieces. Sending thread can send in bursts with delay or in uniform manner.
