import psutil
import scapy.all as scapy
import socket
import struct
import fcntl
from .ensure_admin import elevate_and_run  # relative
from .device_info import detect_os_via_ttl  # relative
import platform
from utils.colors import YELLOW, RESET, MAGENTA, DCYAN, GREEN, IBLUE, DWHITE


def get_ip_address(interface="wlan0"):
    """
    Gets the IP address of a network device using iproute2.
    Handles the case where the device might not have an IP address yet.

    Args:
        device (str): The name of the network device.

    Returns:
        str: The IP address of the device, or an empty string if not found.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ip = fcntl.ioctl(sock.fileno(), 0x8915, struct.pack(
            '256s', interface[:15].encode()))[20:24]
        return socket.inet_ntoa(ip)
    except IOError:
        return None  # Interface not found or not connected


def get_subnet(ip):
    """Derive the subnet from the given IP address."""
    if ip.startswith("10."):
        return "10.0.0.0/8"
    elif ip.startswith("172.16.") or ip.startswith("172.31."):
        return "172.16.0.0/12"
    elif ip.startswith("192.168."):
        return f"{'.'.join(ip.split('.')[:3])}.0/24"
    else:
        return f"{'.'.join(ip.split('.')[:3])}.0/24"  # Default to class C


def scan_network(ip_range="192.168.0/24") -> list:
    """Scan the network for active devices using ARP requests."""
    arp_request = scapy.ARP(pdst=ip_range)
    broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = broadcast / arp_request
    result = scapy.srp(packet, timeout=3, verbose=0)[0]
    devices = []
    for sent, received in result:
        devices.append({'ip': received.psrc, 'mac': received.hwsrc})
    return devices


def get_all_mac_addresses() -> dict:
    """Returns MAC addresses for all available network interfaces."""
    mac_addresses = {}
    for interface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == psutil.AF_LINK:  # Check if it's a MAC address
                mac_addresses[interface] = addr.address
    return mac_addresses


def get_local_ip(hostname=socket.gethostname()):
    """Returns the local IP address of the machine."""
    return socket.gethostbyname(hostname)


def get_correct_local_ip():
    """Gets the actual IP address used to connect to the network."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        # Google's DNS, used only to get the correct interface
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]


def sharingDevices(devices: list, port=9001, timeout=1) -> list:
    """ Add my ip && mac address to devices list"""
    my_mac = get_all_mac_addresses()
    my_ip = get_correct_local_ip()
    _os = detect_os_via_ttl(my_ip)
    if devices:
        devices.append(
            {'ip': my_ip, 'mac': my_mac['wlan0'], 'os_type': _os if _os else platform.system()})
    else:
        devices = [{'ip': my_ip, 'mac': my_mac['wlan0'],
                    'os_type': _os if _os else platform.system()}]

    sharing_dev = []
    sharing_dev_dict = []
    for device in devices:
        """Check if a specific port is open on a given device."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        # Returns 0 if open, otherwise an error code
        result = sock.connect_ex((device['ip'], port))
        sock.close()
        if result == 0:
            sharing_dev.append(device)
            sharing_dev_dict.append(
                {'ip': my_ip, 'mac': my_mac['wlan0'], 'os_type': _os if _os else platform.system()})

    print(f"[{DCYAN}Sharing Hosts{RESET}]")
    if sharing_dev_dict:
        for device in sharing_dev_dict:
            print(
                f"IP: {GREEN}{device['ip']}{RESET}, MAC: {MAGENTA}{device['mac']}{RESET}, OS: {YELLOW}{device['os_type']}{RESET}")

    return sharing_dev if sharing_dev else None


def simulator(sharing_devices: list = None) -> list:
    sharing_devices = [] if not sharing_devices else sharing_devices
    if sharing_devices:
        sharing_devices.append(
            {'ip': "192.168.1.101", 'mac': '', 'os_type': platform.system()})
        sharing_devices.append(
            {'ip': "192.168.1.102", 'mac': '', 'os_type': platform.system()})
        sharing_devices.append(
            {'ip': "192.168.1.103", 'mac': '', 'os_type': platform.system()})
        sharing_devices.append(
            {'ip': "192.168.1.104", 'mac': '', 'os_type': platform.system()})
        sharing_devices.append(
            {'ip': "192.168.1.105", 'mac': '', 'os_type': platform.system()})
    if not sharing_devices:
        sharing_devices = [{'ip': "192.168.1.101",
                            'mac': '', 'os_type': platform.system()},
                           {'ip': "192.168.1.102",
                            'mac': '', 'os_type': platform.system()},
                           {'ip': "192.168.1.103",
                            'mac': '', 'os_type': platform.system()},
                           {'ip': "192.168.1.104",
                            'mac': '', 'os_type': platform.system()},
                           {'ip': "192.168.1.105",
                            'mac': '', 'os_type': platform.system()}]

    return sharing_devices


def main(interface: str = "wlan0", simulate: bool = False) -> list:
    # Automatically get the IP and subnet range
    print(f"[{IBLUE}Get{RESET}] {DWHITE}Subnet ...{RESET}")
    local_ip = get_ip_address(interface)

    if local_ip:
        subnet = get_subnet(local_ip)
        print(
            f"[{IBLUE}***{RESET}] {DWHITE} Scanning network: {YELLOW}{subnet}...{RESET}")
        devices = elevate_and_run(scan_network, subnet)
        if devices:
            print(f"[{DCYAN}All Hosts{RESET}]")
            for device in devices:
                device = {'ip': device['ip'], 'mac': device['mac'],
                          'os_type': detect_os_via_ttl(device['ip'])}
                print(
                    f"IP: {GREEN}{device['ip']}{RESET}, MAC: {MAGENTA}{device['mac']}{RESET}, OS: {YELLOW}{device['os_type']}{RESET}")

        sharing_devices = sharingDevices(devices)

        if simulate:
            sharing_devices = simulator(sharing_devices)
        print(f"[{DCYAN}Sharing Hosts{RESET}]")
        if sharing_devices:
            for device in sharing_devices:
                print(
                    f"IP: {GREEN}{device['ip']}{RESET}, MAC: {MAGENTA}{device['mac']}{RESET}, OS: {YELLOW}{device['os_type']}{RESET}")
        return sharing_devices
    else:
        print("Could not determine local IP. Check your network connection.")
        return []


if __name__ == "__main__":
    main()
