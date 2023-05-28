import argparse
import nmap
import socket

def get_local_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 8000))
        return s.getsockname()[0]

def discover_ips_on_network(local_ip): 
    network_prefix = '.'.join(local_ip.split('.')[:-1])
    target_ip = f"{network_prefix}.0/24"
    
    nm = nmap.PortScanner()
    nm.scan(hosts=target_ip, arguments='-n -sS -p 8000')
    ips = [host for host in nm.all_hosts() if nm[host].has_tcp(8000) and nm[host]['tcp'][8000]['state'] == 'open' and host != local_ip]


    return ips

def discover_ips_on_mosquitto(local_ip): 
    network_prefix = '.'.join(local_ip.split('.')[:-1])
    target_ip = f"{network_prefix}.0/24"
    
    nm = nmap.PortScanner()
    nm.scan(hosts=target_ip, arguments='-n -sS -p 1883')
    ips = [host for host in nm.all_hosts() if nm[host].has_tcp(1883) and nm[host]['tcp'][1883]['state'] == 'open']

    if ips:
        return ips[0]
    else:
        return None

def discoverIPS():
    local_ip = get_local_ip() 
    ips = discover_ips_on_network(local_ip)
    return ips

def attributeRole():
    parser = argparse.ArgumentParser(description="Enter the role of this instance (smartswitch or lightbulb)")
    parser.add_argument("role", type=str, help="Role of this instance")
    args = parser.parse_args()

    if args.role == "smartswitch" or "lightbulb":
        return args.role
    else:
        print("Invalid role. Please enter either 'smartswitch' or 'lightbulb'")
        return None

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
