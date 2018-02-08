"""
file: project3.py
language: python3

This program can be used to send ping and traceroute requests using python raw packets.
"""

import binascii
import os
import random
import socket
import struct
import sys
import time

# Constants
tab = '\t'
INFINITE = sys.maxsize
DEFAULT_PAYLOAD = 32
DEFAULT_BUFFER = 1024
DEFAULT_PORT = 0
DEFAULT_TIMEOUT = 3


def binary_equivalent(hex):
    """
    Finds a binary equivalent of a hexadecimal string.
    :param hex: hexadecimal string
    :return: str binary equivalent with leading zeros
    """
    return (bin(int(hex, 16))[2:]).zfill(16)


def one_complement_sum(binary_1, binary_2):
    """
    Computes the one's complement sum on two binary nos by converting them to decimal and then reconverting them.
    If carry is generated, it is truncated from the sum and added to the least significant bit of the sum.
    :param binary_1: number 1
    :param binary_2: number 2
    :return: one's complement sum
    """
    sum = bin(int(binary_1, 2) + int(binary_2, 2))[2:].zfill(16)
    if len(sum) == 16:
        return sum
    else:
        return one_complement_sum(sum[1:], sum[0])


def calculate_checksum(packet):
    """
    Calculates checksum by converting the byte array to hexdump and creating chunks of 4 hex which would correspond to
    16 bit binary equivalent. It then adds them following the one's complement sum algorithm.
    :param packet: packet to be sent
    :return: int checksum
    """
    parts = []
    hexdump = binascii.hexlify(packet)
    hexdump = hexdump.decode("utf-8")
    j = 0

    for i in range((len(hexdump) // 4)):
        parts.append(binary_equivalent(hexdump[j:j + 4]))
        j += 4

    # handling the remaining hex, if any, padding them with 0's
    left_over = len(hexdump[j:])
    for i in range(4 - left_over):
        hexdump += "0"

    parts.append(binary_equivalent(hexdump[j:]))

    checksum = one_complement_sum(parts[0], parts[1])
    for i in range(2, len(parts)):
        checksum = one_complement_sum(checksum, parts[i])

    inverted_checksum = ""
    for char in checksum:
        if char == "0":
            inverted_checksum += "1"
        else:
            inverted_checksum += "0"

    return int(inverted_checksum, 2)


def get_ttl(packet):
    """
    Extracts time to live from the received packet.
    :param packet: IP packet
    :return: ttl
    """
    packet = binascii.hexlify(packet).decode("utf-8")
    return str(int(packet[16:18], 16))


def add_payload(size):
    """
    Returns random bytes of length size to create the payload.
    :param size: int size of the payload.
    :return: random bytes of length size.
    """
    return os.urandom(size)


def icmp(seq_no, payload_size):
    """
    Creates an ICMP packet with given sequence number and payload size to be sent by raw socket.
    :param seq_no: int seq no.
    :param payload_size: int size of payload
    :return: icmp packet
    """
    type = 8
    code = 0
    chksum = 0
    id = random.randint(0, 0xFFFF)
    data = add_payload(payload_size)
    real_checksum = calculate_checksum(struct.pack("!BBHHH", type, code, chksum, id, seq_no) + data)
    icmp_pkt = struct.pack("!BBHHH", type, code, real_checksum, id, seq_no)
    return icmp_pkt + data


def ping(host, size, iterations, sleep, timeout):
    """
    Generates ICMP ping requests and wait for timeout seconds for ping replies.
    :param host: String hostname
    :param size: int Size of payload
    :param iterations: Number of packets to ping with
    :param sleep: int time delay between each ping request in seconds
    :param timeout: int timeout of entire program in seconds
    :return: None
    """
    main_start_time = time.time()
    times = []
    try:
        host_ip = socket.gethostbyname(host)
    except socket.gaierror:
        print("Invalid Address")
        exit(1)
    print()
    print("Pinging " + host + " [" + socket.gethostbyname(host) + "] with " + str(size) + " bytes of data:")
    s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    s.settimeout(DEFAULT_TIMEOUT)
    send_count = 0
    received_count = 0
    try:
        for i in range(1, iterations + 1):
            if time.time() - main_start_time > timeout:
                break
            try:
                start = time.time()
                s.sendto(icmp(i, size), (host_ip, DEFAULT_PORT))
                send_count += 1
                packet, address = s.recvfrom(DEFAULT_BUFFER)
                end = time.time()
                round_trip_time = (end - start) * 1000
                times.append(round_trip_time)
                received_payload = len(packet) - 28
                print("Reply from " + host_ip + ": bytes=" + str(received_payload) + " time=" + str(
                    int(round_trip_time)) + "ms" + \
                      " TTL=" + str(get_ttl(packet)))
                received_count += 1
                if time.time() - main_start_time + sleep > timeout:
                    break
                time.sleep(sleep)

            except socket.timeout:
                print("Request timed out.")
    except KeyboardInterrupt:
        pass

    if send_count > 0:
        lost_packets = send_count - received_count
        percent_loss = lost_packets / send_count * 100

        print("Ping statistics for " + host_ip + ":")
        print(tab + "Packets: Sent = " + str(send_count) + ", Received = " + str(received_count) + \
              ", Lost = " + str(lost_packets) + " (" + str(percent_loss) + "% loss),")

    else:
        print("No packets sent.")
        exit(1)

    if len(times) > 0:
        print("Approximate round trip times in milli-seconds:")

        print(tab + "Minimum = " + str(int(min(times))) + "ms, Maximum = " + str(int(max(times))) + "ms, Average = " + \
              str(int(sum(times) / len(times))) + "ms")


def get_type(packet):
    """
    Returns the type in the ICMP header of the given packet.
    :param packet: network packet
    :return: int type
    """
    return int(str(packet[20]))


def traceroute(hostname, no_packets, detailed, not_answered):
    """
    Prints a route to hostname by sending ICMP request with increasing TTL.
    :param hostname: String hostname
    :param no_packets: int No of probes
    :param detailed: Boolean if detailed output required or not
    :param not_answered: Boolean whether or not to print no of packets not responded for
    :return:
    """
    try:
        host_ip = socket.gethostbyname(hostname)
    except socket.gaierror:
        print("Invalid Address")
        exit(1)
    print()
    print("Tracing route to " + hostname + " [" + socket.gethostbyname(hostname) + "]")
    print("over a maximum of 30 hops:")
    print()

    soc = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    soc.settimeout(DEFAULT_TIMEOUT)
    flag = 0
    for ttl in range(1, 31):
        count_responses = 0
        print(ttl, end="\t")
        for i in range(1, no_packets + 1):
            try:
                start = time.time()
                soc.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)
                soc.sendto(icmp(i, DEFAULT_PAYLOAD), (socket.gethostbyname(hostname), DEFAULT_PORT))
                packet, address = soc.recvfrom(DEFAULT_BUFFER)
                end = time.time()
                round_trip_time = (end - start) * 1000
                print(str(int(round_trip_time)) + " ms", end='\t')
                count_responses += 1
                if get_type(packet) == 0:
                    flag = 1
                    # uncomment next line if you want to wait between sending packets.
                    # time.sleep(1)
            except socket.timeout:
                print("*\t", end="\t")

        if not_answered:
            print(str(no_packets - count_responses) + "/" + str(no_packets) + " packets not answered\t", end='')

        if detailed:
            if count_responses != 0:
                try:
                    print(socket.gethostbyaddr(address[0])[0] + " [" + address[0] + "]")
                except socket.herror:
                    print(address[0])
            else:
                print("Request timed out.")

        else:
            if count_responses != 0:
                print(address[0])
            else:
                print("Request timed out.")

        if flag == 1:
            break

    if flag == 1:
        print("Trace complete")
    else:
        print("Unable to reach " + hostname + " in 30 hops")


def ping_test(hostname):
    """
    Processes ping request handling all the options and if not present, using the defaults.
    :param hostname: String hostname
    :return: None
    """
    arguments = {
        "-c": INFINITE,
        "-i": 1,
        "-s": 56,
        "-t": INFINITE
    }

    index = 3
    while index < len(sys.argv):
        if sys.argv[index] not in arguments:
            print("Wrong arguments.")
            exit(1)
        try:
            value = int(sys.argv[index + 1])
        except ValueError:
            print("Value is not Integer")
            exit(1)
        arguments[sys.argv[index]] = int(sys.argv[index + 1])
        index += 2

    ping(hostname, arguments["-s"], arguments["-c"], arguments["-i"], arguments["-t"])


def traceroute_test(hostname):
    """
    Processes traceroute request handling all the options and if not present, using the defaults.
    :param hostname: String hostname
    :return:
    """
    arguments = {
        "-n": True,
        "-q": 3,
        "-S": False,
        "-V": 0
    }
    index = 3
    while index < len(sys.argv):
        if sys.argv[index] not in arguments:
            print("Wrong arguments.")
            exit(1)
        elif sys.argv[index] == '-S':
            arguments['-S'] = True
            index += 1
        elif sys.argv[index] == '-n':
            arguments['-n'] = False
            index += 1
        elif sys.argv[index] == '-q':
            arguments['-q'] = int(sys.argv[index + 1])
            index += 2

    traceroute(hostname, arguments["-q"], arguments["-n"], arguments["-S"])


def main():
    """
    The main program which determines type of request.
    :return: None
    """
    if len(sys.argv) < 3:  # checking for commandline arguments
        print("Please enter a host name.")
        exit(1)

    hostname = sys.argv[2]

    if sys.argv[1] == "ping":
        ping_test(hostname)
    elif sys.argv[1] == "traceroute":
        traceroute_test(hostname)
    else:
        print("I can only ping and traceroute for now!")
        exit(1)


if __name__ == '__main__':
    main()
