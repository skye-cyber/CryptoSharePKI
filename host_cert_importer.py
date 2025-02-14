import os
import subprocess

# Configuration
host_name = "172.17.88.189"  # Change this to you machine's ip address
pfx_file = f"{host_name}.pfx" # Replace with your host's file name
root_ca_file = "rootCA.pem"  # Root CA file
pfx_password = "skyepass"  # Replace or retrieve securely
cert_dir = "/etc/ssl/certs/"
key_dir = "/etc/ssl/private/"

# Step 1: Extract Private Key and Certificate
try:
    print("Extracting private key and certificate...")
    subprocess.run(
        ["openssl", "pkcs12", "-in", pfx_file, "-out", f"{cert_dir}host1.crt", "-clcerts", "-nokeys", "-passin", f"pass:{pfx_password}"],
        check=True
    )
    subprocess.run(
        ["openssl", "pkcs12", "-in", pfx_file, "-out", f"{key_dir}host1.key", "-nocerts", "-nodes", "-passin", f"pass:{pfx_password}"],
        check=True
    )
    print("Certificate and key extracted successfully!")
except subprocess.CalledProcessError as e:
    print(f"Error extracting files: {e}")
    exit(1)

# Step 2: Install Root CA to Trusted Store
try:
    print("Installing Root CA to trusted store...")
    subprocess.run(["cp", root_ca_file, f"{cert_dir}"], check=True)
    subprocess.run(["update-ca-certificates"], check=True)  # For Debian-based distros
    print("Root CA installed successfully!")
except subprocess.CalledProcessError as e:
    print(f"Error installing Root CA: {e}")
    exit(1)

print("Certificate import process completed!")
