import socket
import sys
import time
import argparse
from collections import defaultdict

def handshake(peer_ips, port=5000, retries=3):
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    my_socket.bind(('', port))

    role_counts = defaultdict(int)
    role = None

    retries_left = retries
    while retries_left > 0:
        # Send join message to all other instances
        for peer_ip in peer_ips:
            my_socket.sendto("join".encode('utf-8'), (peer_ip, port))

        # Wait for responses from other instances
        try:
            my_socket.settimeout(3)  # Wait up to 3 seconds for responses
            while True:
                data, addr = my_socket.recvfrom(1024)
                peer_role = data.decode('utf-8')
                role_counts[peer_role] += 1

        except socket.timeout:
            if not role_counts:
                # No responses received, retry the handshake
                retries_left -= 1
                time.sleep(1)
            else:
                # Determine role based on received responses
                if role_counts["smartswitch"] == 0:
                    role = "smartswitch"
                else:
                    lightbulb_count = sum(v for k, v in role_counts.items() if k.startswith("lightbulb"))
                    role = f"lightbulb{lightbulb_count + 1}"
                print(f"Handshake successful, starting as {role}")
                return role

    print(f"Handshake failed after {retries} retries, terminating")
    return None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Enter the IP addresses of the other instances")
    parser.add_argument("peer_ips", type=str, nargs='+', help="IP addresses of the other instances")
    args = parser.parse_args()

    role = handshake(args.peer_ips)
    if role:
        if role == "smartswitch":
            # Code for smartswitch behavior
            pass
        elif role.startswith("lightbulb"):
            # Code for lightbulb behavior
            pass
    else:
        print("Handshake failed, exiting")
        sys.exit(1)
