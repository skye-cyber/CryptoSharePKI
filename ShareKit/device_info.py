import os
import platform
import socket
import requests


def get_device_vendor(mac_address):
    url = f"https://api.macvendors.com/{mac_address}"
    try:
        response = requests.get(url)
        print(response)
        return response.text if response.status_code == 200 else "Unknown"
    except Exception:
        return "Lookup failed"


def get_vendor_by_open_ports(ip):
    common_ports = [22, 3389, 445, 9100, 62078]
    device_type = "Unknown"
    for port in common_ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((ip, port))
        sock.close()
        if result == 0:
            if port == 22:
                device_type = "Linux or macOS (SSH)"
            elif port == 3389:
                device_type = "Windows PC (RDP)"
            elif port == 445:
                device_type = "Windows or Network Storage (SMB)"
            elif port == 9100:
                device_type = "Printer"
            elif port == 62078:
                device_type = "iPhone or iPad"
    return device_type


def detect_os_via_ttl(ip):
    ping_cmd = f"ping -c 1 {ip}" if platform.system(
    ) != "Windows" else f"ping -n 1 {ip}"
    result = os.popen(ping_cmd).read()

    if "TTL=128" in result.upper():
        return "Windows"
    elif "TTL=64" in result.upper():
        return "Linux/macOS"
    elif "TTL=255" in result.upper():
        return "Cisco Device"
    return "Unknown OS"


if __name__ == "__main__":
    print(detect_os_via_ttl("192.168.43.10"))
    # print(get_device_vendor("06:3a:55:04:5e:d9"))  # Example Apple MAC
