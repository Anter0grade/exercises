import socket
import struct
import random
import time
import ipaddress

DNS_SERVER = "1.1.1.1"
DNS_PORT = 53
TIMEOUT = 4

RECORD_TYPES = {
    "A": 1,
    "NS": 2,
    "CNAME": 5,
    "SOA": 6,
    "PTR": 12,
    "MX": 15,
    "TXT": 16,
    "AAAA": 28,
    "SRV": 33,
    "CAA": 257
}

RECORD_NAMES = {v: k for k, v in RECORD_TYPES.items()}


'''
what I learned

A       = maps a domain name to an ipv4 addr
AAAA    = maps a domain name to an ipv6 addr
MX      = mail exchange record, mail server which receives mail for a domain
NS      = name server record, dns server resposible for a domain
TXT     = stores text information ascosiated with a domain
CNAME   = cononical name record, makes one domain name an alias of another
PTR     = pointer record used for reverse DNS lookup

reverse dns is looking up a domain name using an ip addr, commonly using 
a PTR record

port 53: dns port

packets are encoded & decoded because they need a standard binary format 

socket = ip, port & protocol

'''



# dns name encoding

def encode_domain(domain):

    domain = domain.rstrip(".")

    if not domain:
        raise ValueError("Domain cannot be empty")

    encoded = b""

    for label in domain.split("."):

        label = label.encode("idna")

        if len(label) > 63:
            raise ValueError("DNS label exceeds 63 bytes")

        encoded += bytes([len(label)]) + label

    encoded += b"\x00"

    if len(encoded) > 255:
        raise ValueError("DNS name is too long")

    return encoded


# dns name decoding
# Handles compressed DNS names

def decode_domain(data, offset):

    labels = []
    jumped = False
    next_offset = offset
    visited = set()

    while True:

        if offset >= len(data):
            raise ValueError("Invalid DNS name")

        length = data[offset]

        # End of name
        if length == 0:

            if not jumped:
                next_offset = offset + 1

            break

        # Compression pointer
        if length & 0xC0 == 0xC0:

            if offset + 1 >= len(data):
                raise ValueError("Invalid compression pointer")

            pointer = ((length & 0x3F) << 8) | data[offset + 1]

            if pointer in visited or pointer >= len(data):
                raise ValueError("Invalid DNS compression")

            visited.add(pointer)

            if not jumped:
                next_offset = offset + 2

            offset = pointer
            jumped = True
            continue

        if length & 0xC0:
            raise ValueError("Invalid DNS label")

        offset += 1

        if offset + length > len(data):
            raise ValueError("Truncated DNS name")

        label = data[offset:offset + length]

        labels.append(label.decode("ascii", errors="replace"))

        offset += length

        if not jumped:
            next_offset = offset

    return ".".join(labels), next_offset


# dns query builder

def build_query(domain, record_type):

    transaction_id = random.randint(0, 65535)

    # Dns header
    flags = 0x0100  # Recursion desired

    header = struct.pack(
        "!HHHHHH",
        transaction_id,
        flags,
        1,  # Questions
        0,  # Answers
        0,  # Authority
        0   # Additional
    )

    question = encode_domain(domain)

    question += struct.pack(
        "!HH",
        record_type,
        1  # Internet class
    )

    return transaction_id, header + question


# ==========================================
# DNS RESPONSE PARSER
# ==========================================

def parse_record(data, offset):

    name, offset = decode_domain(data, offset)

    if offset + 10 > len(data):
        raise ValueError("Truncated resource record")

    record_type, record_class, ttl, rdlength = struct.unpack(
        "!HHIH", data[offset:offset + 10]
    )

    offset += 10

    end = offset + rdlength

    if end > len(data):
        raise ValueError("Truncated record data")

    rdata = data[offset:end]

    record_value = None

    if record_type == 1 and rdlength == 4:
        record_value = socket.inet_ntop(
            socket.AF_INET, rdata
        )

    elif record_type == 28 and rdlength == 16:
        record_value = socket.inet_ntop(
            socket.AF_INET6, rdata
        )

    elif record_type in (2, 5, 12):
        record_value, _ = decode_domain(data, offset)

    elif record_type == 15 and rdlength >= 3:

        preference = struct.unpack("!H", rdata[:2])[0]

        exchange, _ = decode_domain(data, offset + 2)

        record_value = {
            "preference": preference,
            "exchange": exchange
        }

    elif record_type == 16:

        strings = []
        position = 0

        while position < len(rdata):

            length = rdata[position]
            position += 1

            if position + length > len(rdata):
                raise ValueError("Invalid TXT record")

            strings.append(
                rdata[position:position + length].decode(
                    "utf-8", errors="replace"
                )
            )

            position += length

        record_value = strings

    elif record_type == 6:

        mname, pos = decode_domain(data, offset)
        rname, pos = decode_domain(data, pos)

        if pos + 20 > end:
            raise ValueError("Invalid SOA record")

        serial, refresh, retry, expire, minimum = struct.unpack(
            "!IIIII", data[pos:pos + 20]
        )

        record_value = {
            "primary": mname,
            "responsible": rname,
            "serial": serial,
            "refresh": refresh,
            "retry": retry,
            "expire": expire,
            "minimum": minimum
        }

    elif record_type == 33 and rdlength >= 7:

        priority, weight, port = struct.unpack(
            "!HHH", rdata[:6]
        )

        target, _ = decode_domain(data, offset + 6)

        record_value = {
            "priority": priority,
            "weight": weight,
            "port": port,
            "target": target
        }

    elif record_type == 257 and rdlength >= 2:

        flags = rdata[0]
        tag_length = rdata[1]

        if 2 + tag_length <= rdlength:
            tag = rdata[2:2 + tag_length].decode(
                "ascii", errors="replace"
            )

            value = rdata[2 + tag_length:].decode(
                "utf-8", errors="replace"
            )

            record_value = {
                "flags": flags,
                "tag": tag,
                "value": value
            }

    if record_value is None:
        record_value = rdata.hex()

    record = {
        "name": name,
        "type": RECORD_NAMES.get(record_type, str(record_type)),
        "ttl": ttl,
        "class": record_class,
        "data": record_value
    }

    return record, end


def parse_response(data, expected_id):

    if len(data) < 12:
        raise ValueError("DNS response too short")

    transaction_id, flags, qd, an, ns, ar = struct.unpack(
        "!HHHHHH", data[:12]
    )

    if transaction_id != expected_id:
        raise ValueError("DNS transaction ID mismatch")

    if not flags & 0x8000:
        raise ValueError("Packet is not a DNS response")

    rcode = flags & 0x000F

    rcode_names = {
        0: "NOERROR",
        1: "FORMERR",
        2: "SERVFAIL",
        3: "NXDOMAIN",
        4: "NOTIMP",
        5: "REFUSED"
    }

    result = {
        "rcode": rcode_names.get(rcode, f"RCODE {rcode}"),
        "authoritative": bool(flags & 0x0400),
        "recursion_available": bool(flags & 0x0080),
        "truncated": bool(flags & 0x0200),
        "records": {
            "Answer": [],
            "Authority": [],
            "Additional": []
        }
    }

    offset = 12

    # Skip question section
    for _ in range(qd):

        _, offset = decode_domain(data, offset)

        if offset + 4 > len(data):
            raise ValueError("Invalid question section")

        offset += 4

    # Parse resource record sections
    sections = [
        ("Answer", an),
        ("Authority", ns),
        ("Additional", ar)
    ]

    for section_name, count in sections:

        for _ in range(count):

            record, offset = parse_record(data, offset)

            result["records"][section_name].append(record)

    return result


# dns net client

def receive_exact(sock, length):

    chunks = []
    received = 0

    while received < length:

        chunk = sock.recv(length - received)

        if not chunk:
            raise ConnectionError("DNS TCP connection closed")

        chunks.append(chunk)
        received += len(chunk)

    return b"".join(chunks)


def dns_query(domain, record_type, server=None):

    server = server or DNS_SERVER

    if record_type not in RECORD_TYPES:
        raise ValueError("Unsupported DNS record type")

    transaction_id, packet = build_query(
        domain, RECORD_TYPES[record_type]
    )

    start = time.perf_counter()

    # Try UDP first
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:

        sock.settimeout(TIMEOUT)

        sock.sendto(packet, (server, DNS_PORT))

        response, _ = sock.recvfrom(65535)

    result = parse_response(response, transaction_id)

    # Retry using TCP if response was truncated
    if result["truncated"]:

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:

            sock.settimeout(TIMEOUT)

            sock.connect((server, DNS_PORT))

            sock.sendall(
                struct.pack("!H", len(packet)) + packet
            )

            response_length = struct.unpack(
                "!H", receive_exact(sock, 2)
            )[0]

            response = receive_exact(sock, response_length)

        result = parse_response(response, transaction_id)

    result["query_time"] = (
        time.perf_counter() - start
    ) * 1000

    result["server"] = server

    return result


def display_results(result):

    print("\n" + "=" * 55)

    print(f"DNS SERVER: {result['server']}")
    print(f"RESPONSE: {result['rcode']}")
    print(f"QUERY TIME: {result['query_time']:.2f} ms")

    print(
        f"AUTHORITATIVE: {result['authoritative']}"
    )

    print(
        f"RECURSION AVAILABLE: {result['recursion_available']}"
    )


    for section, records in result["records"].items():

        print(f"\n--- {section.upper()} ---")

        if not records:
            print("No records found.")
            continue

        for record in records:

            print(f"\nName: {record['name']}")
            print(f"Type: {record['type']}")
            print(f"TTL: {record['ttl']} seconds")
            print(f"Data: {record['data']}")


# reverse dns

def reverse_lookup(ip, server=None):

    try:
        address = ipaddress.ip_address(ip)

        reverse_domain = address.reverse_pointer

        print(f"\nReverse lookup: {reverse_domain}")

        result = dns_query(
            reverse_domain, "PTR", server
        )

        display_results(result)

    except ValueError:
        print("Invalid IP address.")

    except (OSError, ConnectionError, TimeoutError) as error:
        print(f"Network error: {error}")

    except Exception as error:
        print(f"Lookup error: {error}")


def full_investigation(domain, server=None):

    record_types = [
        "A",
        "AAAA",
        "MX",
        "NS",
        "TXT",
        "CNAME",
        "SOA",
        "SRV",
        "CAA"
    ]

    print(f"Domain: {domain}")
    print(f"DNS Server: {server or DNS_SERVER}")

    for record_type in record_types:

        print(f"\n\nCHECKING {record_type} RECORDS...")
        print("-" * 60)

        try:
            result = dns_query(domain, record_type, server)
            display_results(result)

        except (OSError, ConnectionError, TimeoutError) as error:
            print(f"Network error: {error}")

        except Exception as error:
            print(f"Lookup error: {error}")

    print("investigation complete")


def main():
    while True:

        domain = input("\nEnter domain: ").strip()

        if domain.lower() == "exit":
            print("Closing DNS Investigator.")
            break

        if not domain:
            print("Please enter a domain.")
            continue

        try:
            encode_domain(domain)

            full_investigation(domain, DNS_SERVER)

        except (ValueError, UnicodeError) as error:
            print(f"Invalid domain: {error}")

        except KeyboardInterrupt:
            print("\nInvestigation interrupted.")
            break

if __name__ == "__main__":
    main()
