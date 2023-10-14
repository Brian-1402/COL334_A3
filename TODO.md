## Todo:

- Make recv robust to move on when timeout occurs instead of exception and stopping.

- Make the sending and receiving threads.

- check if UDP also has the same issue of data coming halfway and requiring recv in a loop to get complete data, like in TCP in A2.
