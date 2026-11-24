# use on quiet network or raise threshold
# must run with sudo

import subprocess
import time
import socket
from collections import Counter
#Check when tshark stdout has data available avoids blocking read
import selectors
import os

INTERFACE = "wlo1" # change to your net interface
THRESHOLD = 100
INTERVAL = 2 # seconds 

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("10.255.255.255", 1))
    ip = s.getsockname()[0]
    s.close()
    return ip

def parse_line(line, local_ip):
    parts = line.strip().split()
    ips = []
    if len(parts) >= 2:
        src = parts[0]
        dst = parts[1]
        if src != local_ip:
            ips.append(src)
        if dst != local_ip:
            ips.append(dst)
    return ips

# main monitoring
local_ip = get_local_ip()
print("local ip:", local_ip)

process = subprocess.Popen(
    ["tshark", "-i", INTERFACE,
     "-l", "-T", "fields",
     "-e", "ip.src", "-e", "ip.dst", "udp"],
    stdout=subprocess.PIPE
)


selector = selectors.DefaultSelector()
selector.register(process.stdout, selectors.EVENT_READ)

buffer = []
pending = ""

try:
    while True:
        end_time = time.monotonic() + INTERVAL

        while time.monotonic() < end_time:
            if len(buffer) >= THRESHOLD:
                break

            remaining = end_time - time.monotonic()

            events = selector.select(timeout=remaining)

            if not events:
                break

            data = os.read(process.stdout.fileno(), 4096)

            if not data:
                break

            pending += data.decode("utf-8", errors="replace")

            lines = pending.split("\n")
            pending = lines.pop()

            buffer.extend(line for line in lines if line)

        if len(buffer) >= THRESHOLD:
            remote_ips = []

            for line in buffer:
                parsed = parse_line(line, local_ip)

                for ip in parsed:
                    remote_ips.append(ip)

            if remote_ips:
                counts = Counter(remote_ips)
                most_common_ip, count = counts.most_common(1)[0]

                print("\n====================")
                print("Identified :\033[1m\033[92m", most_common_ip, "\033[0m")
                print("\nPacket count in burst :\033[1m\033[91m", count, "\033[0m")

            else:
                print("Threshold reached but no IPs found")
            buffer = []

except KeyboardInterrupt:
    print("\nStopped")

finally:
    selector.close()
    process.terminate()
    process.wait()
    print("tshark process terminated")