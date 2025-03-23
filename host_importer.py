import os
import platform
import subprocess
import warnings

import requests
from colorama import Fore, init
from verifyCATrust import verify_root_ca_trust

# Suppress the InsecureRequestWarning
warnings.filterwarnings(
    "ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)

init(autoRESET=True)

# Determine color constants based on the operating system
if platform.system().lower() == 'windows':
    GREEN = Fore.GREEN
    BLUE = Fore.BLUE
    RED = Fore.RED
    YELLOW = Fore.YELLOW
    CYAN = Fore.CYAN
    MAGENTA = Fore.MAGENTA
    RESET = Fore.RESET
elif platform.system().lower() == 'linux':
    RED = "\033[3;2;91m"
    BLUE = "\033[3;2;94m"
    CYAN = "\033[3;2;96m"
    GREEN = "\033[3;2;92m"
    MAGENTA = "\033[3;2;95m"
    YELLOW = "\033[3;2;93m"
    RESET = "\033[0m"

# Configuration
server_url = "https://172.17.88.189:5000"
host_name = "172.17.88.189"  # this should be changed to the desktop name
pfx_file = f"{host_name}.pfx"
root_ca_file = "CryptoshareRootCA.pem"

# Use local directory for portability
download_dir = os.path.join(os.getcwd(), "certs")
pfx_password = "skyepass"  # You can change the value of password at will but i must be change in the AutoCerGen too

# Detect OS
# 'linux', 'windows', or 'darwin' for macOS
current_os = platform.system().lower()

# Paths based on OS
if current_os == "linux":
    cert_dir = "/etc/ssl/certs/"
    key_dir = "/etc/ssl/private/"
    ca_trust_dir = "/usr/local/share/ca-certificates/"
elif current_os == "windows":
    ca_trust_dir = "C:\\Windows\\System32\\certs\\"
    cert_dir = "C:\\ProgramData\\Certificates\\"
    key_dir = cert_dir  # Windows stores certs and keys together
else:
    raise NotImplementedError(f"OS '{current_os}' not supported.")

# Download files


def download_file(filename):
    url = f"{server_url}/{filename}"
    local_path = os.path.join(download_dir, filename)
    print(f"Downloading {BLUE}{filename}{RESET}...")
    response = requests.get(url, verify=False)  # Disable SSL verification
    if response.status_code == 200:
        with open(local_path, 'wb') as f:
            f.write(response.content)
        print(f"{MAGENTA}{filename}{GREEN} downloaded successfully!{RESET}")
    else:
        print(f"{RED}Failed to download {filename}: {response.status_code}{RESET}")
    return local_path

# Install certificates


def install_certificates(pfx_path, root_ca_path, pfx_password):
    """
    Installs the provided PFX and root CA certificates on the system.

    Args:
        pfx_path (str): Path to the PFX file containing the certificate and key.
        root_ca_path (str): Path to the root CA certificate file.
        pfx_password (str): Password for the PFX file.

    Raises:
        subprocess.CalledProcessError: If any of the subprocess commands fail.
    """
    global host_name, cert_dir, key_dir  # Ensure these variables are defined in the global scope

    if platform.system().lower() == "linux":
        print(f"{GREEN}Installing certificates on Linux...{RESET}")

        try:
            # Extract the certificate from the PFX file
            subprocess.run(
                ["openssl", "pkcs12", "-in", pfx_path, "-out", os.path.join(
                    cert_dir, f"{host_name}.crt"), "-clcerts", "-nokeys", "-passin", f"pass:{pfx_password}"],
                check=True
            )

            # Extract the key from the PFX file
            subprocess.run(
                ["openssl", "pkcs12", "-in", pfx_path, "-out", os.path.join(
                    key_dir, f"{host_name}.key"), "-nocerts", "-nodes", "-passin", f"pass:{pfx_password}"],
                check=True
            )

            # Copy the root CA certificate to the system's CA directory
            subprocess.run(
                ["cp", root_ca_path, ca_trust_dir],
                check=True
            )

            # Update the system's CA certificates
            subprocess.run(["update-ca-certificates"], check=True)

            print(f"{GREEN}Certificates installed successfully on Linux!{RESET}")

        except subprocess.CalledProcessError as e:
            print(f"{RED}Error during Linux certificate installation: {e}{RESET}")

    elif platform.system().lower() == "windows":
        print(f"{YELLOW}Installing certificates on Windows...{RESET}")

        try:
            # Import the PFX file into the Windows certificate store
            subprocess.run(
                ["certutil", "-importpfx", "-f",
                    pfx_path, "Root", "-p", pfx_password],
                check=True
            )

            # Add the root CA certificate to the Windows certificate store
            subprocess.run(
                ["certutil", "-addstore", "Root", root_ca_path],
                check=True
            )

            print("Certificates installed successfully on Windows!")

        except subprocess.CalledProcessError as e:
            print(f"{RED}Error during Windows certificate installation: {e}{RESET}")

    else:
        raise NotImplementedError(
            f"OS '{platform.system().lower()}' not supported.")


# Main
if __name__ == "__main__":
    os.makedirs(download_dir, exist_ok=True)
    pfx_path = download_file(pfx_file)
    root_ca_path = download_file(root_ca_file)
    install_certificates(pfx_path, root_ca_path, pfx_password)
    try:
        is_trusted = verify_root_ca_trust(root_ca_path)
        if is_trusted:
            print(f"{GREEN}Root CA verification succeeded!{RESET}")
        else:
            print(f"{RED}Root CA verification failed.{RESET}")
    except FileNotFoundError as e:
        print(e)
    except NotImplementedError as e:
        print(e)
