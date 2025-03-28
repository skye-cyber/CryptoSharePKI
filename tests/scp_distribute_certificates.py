import os
import subprocess
import json

# Configuration
with open('hosts.json', 'r') as config:
    hosts = json.load(config)

root_ca_file = "rootCA.pem"
remote_cert_dir = "/tmp/"  # Directory on the host where files will be copied

# Transfer certificates to each host
for host_config in hosts:
    host = host_config["host"]
    user = host_config["user"]
    pfx_file = host_config["pfx_file"]

    print(f"Transferring files to {host}...")

    try:
        # Transfer .pfx file
        subprocess.run(["scp", pfx_file, f"{user}@{host}:{remote_cert_dir}"], check=True)
        # Transfer Root CA
        subprocess.run(["scp", root_ca_file, f"{user}@{host}:{remote_cert_dir}"], check=True)

        print(f"Files transferRED to {host} successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error transferring files to {host}: {e}")
