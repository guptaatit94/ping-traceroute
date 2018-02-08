# ping-traceroute
This program can be used to send ping and traceroute requests using python raw packets supporting the mentioned options.

Language: Python3

Please follow these steps to run this project:

Note:
1. Needs sudo privileges.
2. If running on a windows machine, you might need to turn off your firewall.

To run ping:

Step 1: Use the following command
        sudo python3 project3.py ping <hostname> <options>
        For eg.
        sudo python3 project3.py ping www.google.com -c 4 -s 32

Options:

1.  -c : Send count number of packets to ping. Shouldn't be negative. Default is infinite. Use Ctrl + C to quit.
    Format: -c <int>
    Eg. -c 10

2.  -i : waits for specified seconds between requests. Default is 1. Shouldn't be negative.
    Format: -i <int>
    Eg. -i 0

3. -s : Specify size of packet in bytes. Default is 56 bytes. Shouldn't be negative.
    Format: -s <int>
    Eg. -s 32

4. -t : Timeout for entire program in seconds. Shouldn't be negative. Default is infinite.
    Format: -t <int>
    Eg. -t 10


To run traceroute:


Step 1: Use the following command
        sudo python3 project3.py traceroute <hostname> <options>
        For eg.
        sudo python3 project3.py traceroute www.google.com -S -q 2

Options:

1.  -n : If this is specified, the IP address is not resolved i.e. it is printed directly.
    Format: -n

2.  -q : Specify the number of probes to be sent per ttl.
    Format: -q <int>
    Eg. -t 5

3.  -S : If this is specified, it will print number of probes who reached timeout per ttl
    Format: -S

