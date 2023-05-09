from scapy.all import ARP, Ether, srp
import socket

def get_local_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]

def discover_ips_on_network(local_ip):
    network_prefix = '.'.join(local_ip.split('.')[:-1])
    target_ip = f"{network_prefix}.0/24"
    arp = ARP(pdst=target_ip)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether / arp

    result = srp(packet, timeout=3, verbose=0)[0]

    ips = []
    for _, received in result:
        if received.psrc != local_ip:
            ips.append(received.psrc)

    return ips

def discoverIPS():
    local_ip = get_local_ip()
    ips = discover_ips_on_network(local_ip)
    return ips

def main():
    local_ip = get_local_ip()
    print(f"Local IP: {local_ip}")
    print("Discovering IPs on the network...")
    
    ips = discover_ips_on_network(local_ip)
    print("Active IPs on the network:")
    for ip in ips:
        print(ip)

if __name__ == "__main__":
    main()
